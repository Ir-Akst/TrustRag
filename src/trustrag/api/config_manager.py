"""Safe whitelisted runtime configuration management with validation, backup, and audit logging."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from trustrag.api.audit import AuditLogStore
from trustrag.api.schemas import (
    ConfigDiffEntry,
    ConfigFieldMeta,
    ConfigSnapshotResponse,
    ConfigUpdateRequest,
    ConfigUpdateResponse,
)
from trustrag.config import Settings, load_config


@dataclass(frozen=True)
class _EditableSpec:
    section: str
    field: str
    value_type: str
    restart_required: bool
    description: str
    min_val: float | None = None
    max_val: float | None = None
    allowed_values: tuple[str, ...] | None = None


_EDITABLE_SPECS: dict[str, _EditableSpec] = {
    "retrieval.top_k": _EditableSpec(
        section="retrieval",
        field="top_k",
        value_type="int",
        restart_required=False,
        description="Number of evidence documents retrieved per query (1..20).",
        min_val=1,
        max_val=20,
    ),
    "guardrails.enable_paraphrasing": _EditableSpec(
        section="guardrails",
        field="enable_paraphrasing",
        value_type="bool",
        restart_required=False,
        description="Enable G1 controlled semantic-validated query paraphrasing.",
    ),
    "guardrails.paraphrase_backend": _EditableSpec(
        section="guardrails",
        field="paraphrase_backend",
        value_type="str",
        restart_required=False,
        description="G1 paraphrase backend ('disabled' or 'deterministic').",
        allowed_values=("disabled", "deterministic"),
    ),
    "verification.enable_query_consistency": _EditableSpec(
        section="verification",
        field="enable_query_consistency",
        value_type="bool",
        restart_required=False,
        description="Enable G3 answer-to-query consistency verification.",
    ),
    "verification.enable_reanswer": _EditableSpec(
        section="verification",
        field="enable_reanswer",
        value_type="bool",
        restart_required=False,
        description="Enable bounded high-trust re-answer loop on inconclusive G3.",
    ),
    "srm.timeout_seconds": _EditableSpec(
        section="srm",
        field="timeout_seconds",
        value_type="float",
        restart_required=False,
        description="Bounded timeout in seconds for SRM invocations (0.5..30.0).",
        min_val=0.5,
        max_val=30.0,
    ),
    "srm.backend": _EditableSpec(
        section="srm",
        field="backend",
        value_type="str",
        restart_required=True,
        description="Configured SRM backend ('disabled' or 'hf_local'; requires restart/re-init).",
        allowed_values=("disabled", "hf_local"),
    ),
}

_IMMUTABLE_INVARIANTS: list[str] = [
    "guardrails.enabled=True (G1 cannot be disabled via UI/API)",
    "guardrails.block_on_empty=True",
    "retrieval.enforce_removal_cap=True",
    "retrieval.removal_cap_ratio<=0.5",
    "msd.enable_freq_density=False (FilterRAG remains isolated)",
    "srm.trust_remote_code=False",
]


class RuntimeConfigManager:
    """Manages validated runtime configuration updates with backups and audit trail."""

    def __init__(
        self,
        settings: Settings,
        *,
        audit_store: AuditLogStore,
        backup_dir: str | Path = "configs/backups",
        baseline_settings: Settings | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._settings = settings.model_copy(deep=True)
        self._baseline = (baseline_settings or load_config()).model_copy(deep=True)
        self._audit = audit_store
        self._backup_dir = Path(backup_dir)
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        self._backup_count = len(list(self._backup_dir.glob("config_backup_*.json")))

    @property
    def settings(self) -> Settings:
        with self._lock:
            return self._settings.model_copy(deep=True)

    def _get_field(self, cfg: Settings, section: str, field: str) -> Any:
        sec_obj = getattr(cfg, section)
        return getattr(sec_obj, field)

    def _sanitized_effective_dict(self, cfg: Settings) -> dict[str, Any]:
        raw = cfg.model_dump()
        # Strip any provider API keys / secret fields defensively
        if "llm" in raw and isinstance(raw["llm"], dict):
            raw["llm"].pop("api_key", None)
        return raw

    def snapshot(self) -> ConfigSnapshotResponse:
        with self._lock:
            fields: list[ConfigFieldMeta] = []
            for key, spec in _EDITABLE_SPECS.items():
                fields.append(
                    ConfigFieldMeta(
                        key=key,
                        section=spec.section,
                        field=spec.field,
                        current_value=self._get_field(self._settings, spec.section, spec.field),
                        default_value=self._get_field(self._baseline, spec.section, spec.field),
                        value_type=spec.value_type,
                        restart_required=spec.restart_required,
                        description=spec.description,
                    )
                )
            return ConfigSnapshotResponse(
                effective_config=self._sanitized_effective_dict(self._settings),
                editable_fields=fields,
                immutable_security_invariants=list(_IMMUTABLE_INVARIANTS),
                backup_count=self._backup_count,
            )

    def validate_changes(self, changes: dict[str, Any]) -> tuple[bool, list[ConfigDiffEntry], list[str]]:
        errors: list[str] = []
        diffs: list[ConfigDiffEntry] = []
        with self._lock:
            for key, new_val in changes.items():
                spec = _EDITABLE_SPECS.get(key)
                if spec is None:
                    errors.append(
                        f"Setting '{key}' is either unsupported or protected by security invariants."
                    )
                    continue
                if spec.value_type == "bool":
                    if not isinstance(new_val, bool):
                        errors.append(f"'{key}' requires a boolean value.")
                        continue
                elif spec.value_type == "int":
                    if isinstance(new_val, bool) or not isinstance(new_val, int):
                        errors.append(f"'{key}' requires an integer value.")
                        continue
                    if spec.min_val is not None and new_val < spec.min_val:
                        errors.append(f"'{key}' must be >= {int(spec.min_val)}.")
                        continue
                    if spec.max_val is not None and new_val > spec.max_val:
                        errors.append(f"'{key}' must be <= {int(spec.max_val)}.")
                        continue
                elif spec.value_type == "float":
                    if isinstance(new_val, bool) or not isinstance(new_val, (int, float)):
                        errors.append(f"'{key}' requires a numeric value.")
                        continue
                    fval = float(new_val)
                    if spec.min_val is not None and fval < spec.min_val:
                        errors.append(f"'{key}' must be >= {spec.min_val}.")
                        continue
                    if spec.max_val is not None and fval > spec.max_val:
                        errors.append(f"'{key}' must be <= {spec.max_val}.")
                        continue
                    new_val = fval
                elif spec.value_type == "str":
                    if not isinstance(new_val, str):
                        errors.append(f"'{key}' requires a string value.")
                        continue
                    if spec.allowed_values is not None and new_val not in spec.allowed_values:
                        errors.append(f"'{key}' must be one of {list(spec.allowed_values)}.")
                        continue

                old_val = self._get_field(self._settings, spec.section, spec.field)
                diffs.append(
                    ConfigDiffEntry(
                        key=key,
                        old_value=old_val,
                        new_value=new_val,
                        restart_required=spec.restart_required,
                    )
                )
        return (len(errors) == 0), diffs, errors

    def _save_backup_locked(self) -> str:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        self._backup_count += 1
        fname = f"config_backup_{ts}_{self._backup_count:04d}.json"
        target = self._backup_dir / fname
        target.write_text(
            json.dumps(self._sanitized_effective_dict(self._settings), indent=2),
            encoding="utf-8",
        )
        return fname

    def apply_changes(
        self,
        req: ConfigUpdateRequest,
        *,
        request_id: str,
        on_apply: Any = None,
    ) -> ConfigUpdateResponse:
        with self._lock:
            valid, diffs, errors = self.validate_changes(req.changes)
            if not valid:
                return ConfigUpdateResponse(valid=False, applied=False, errors=errors)
            restart_needed = any(d.restart_required for d in diffs)
            if not req.confirm:
                return ConfigUpdateResponse(
                    valid=True,
                    applied=False,
                    requires_confirmation=True,
                    restart_required=restart_needed,
                    diffs=diffs,
                )

            backup_name = self._save_backup_locked()
            candidate = self._settings.model_copy(deep=True)
            for diff in diffs:
                spec = _EDITABLE_SPECS[diff.key]
                sec_obj = getattr(candidate, spec.section)
                setattr(sec_obj, spec.field, diff.new_value)

            # Re-validate full Settings invariants
            validated = Settings.model_validate(candidate.model_dump())
            self._settings = validated
            if on_apply is not None:
                on_apply(self._settings.model_copy(deep=True))

            self._audit.record(
                request_id=request_id,
                event_category="CONFIG_UPDATE",
                component="config_manager",
                decision="APPLIED",
                outcome=f"Updated {len(diffs)} setting(s) by actor='{req.actor}'",
                explanation="; ".join(f"{d.key}: {d.old_value} -> {d.new_value}" for d in diffs),
                evidence_refs=[backup_name],
            )
            return ConfigUpdateResponse(
                valid=True,
                applied=True,
                requires_confirmation=False,
                restart_required=restart_needed,
                backup_path=backup_name,
                diffs=diffs,
            )

    def restore_defaults(
        self,
        *,
        confirm: bool,
        actor: str,
        request_id: str,
        on_apply: Any = None,
    ) -> ConfigUpdateResponse:
        with self._lock:
            diffs: list[ConfigDiffEntry] = []
            for key, spec in _EDITABLE_SPECS.items():
                old_val = self._get_field(self._settings, spec.section, spec.field)
                def_val = self._get_field(self._baseline, spec.section, spec.field)
                if old_val != def_val:
                    diffs.append(
                        ConfigDiffEntry(
                            key=key,
                            old_value=old_val,
                            new_value=def_val,
                            restart_required=spec.restart_required,
                        )
                    )
            restart_needed = any(d.restart_required for d in diffs)
            if not confirm:
                return ConfigUpdateResponse(
                    valid=True,
                    applied=False,
                    requires_confirmation=True,
                    restart_required=restart_needed,
                    diffs=diffs,
                )
            backup_name = self._save_backup_locked()
            self._settings = self._baseline.model_copy(deep=True)
            if on_apply is not None:
                on_apply(self._settings.model_copy(deep=True))
            self._audit.record(
                request_id=request_id,
                event_category="CONFIG_RESTORE",
                component="config_manager",
                decision="RESTORED_DEFAULTS",
                outcome=f"Restored baseline configuration by actor='{actor}'",
                explanation=f"Reverted {len(diffs)} setting(s) to baseline defaults.",
                evidence_refs=[backup_name],
            )
            return ConfigUpdateResponse(
                valid=True,
                applied=True,
                requires_confirmation=False,
                restart_required=restart_needed,
                backup_path=backup_name,
                diffs=diffs,
            )
