"""aiohttp web application factory for TrustRAG Phase 09 API & Dashboard."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aiohttp import web
from pydantic import ValidationError

from trustrag.api.audit import AuditLogStore
from trustrag.api.config_manager import RuntimeConfigManager
from trustrag.api.monitoring import MonitoringTracker
from trustrag.api.schemas import (
    ConfigUpdateRequest,
    EvidenceItemView,
    G1AnalyzeRequest,
    G1AnalyzeResponse,
    G2AnalyzeRequest,
    G2AnalyzeResponse,
    G2DocumentView,
    G3ClaimView,
    G3VerifyRequest,
    G3VerifyResponse,
    PipelineExecuteRequest,
    PipelineExecuteResponse,
    RetrievalEvidenceRequest,
    RetrievalEvidenceResponse,
    SignalDetailView,
    SystemHealthResponse,
    generate_openapi_spec,
)
from trustrag.api.security import SlidingWindowRateLimiter, build_security_middleware, json_error
from trustrag.config import Settings, load_config
from trustrag.detection.msd import MultiSignalDetector
from trustrag.engine.schemas import EvidenceDocument
from trustrag.guardrails.input_guardrail import InputGuardrail
from trustrag.retrieval.retriever import TrustAwareRetriever
from trustrag.serving.service import ProductionQueryRequest, TrustRAGService
from trustrag.verification.output_verifier import OutputEvidenceVerifier

_DEFAULT_CORPUS: list[EvidenceDocument] = [
    EvidenceDocument(
        doc_id="demo_water_01",
        text="At standard sea-level atmospheric pressure, pure water boils at 100 degrees Celsius (212 degrees Fahrenheit).",
        source_id="physics_ref_01",
        provenance="TrustRAG-Demo-Corpus",
        metadata={"verified": True, "source_type": "encyclopedia", "domain": "physics.edu"},
    ),
    EvidenceDocument(
        doc_id="demo_paris_02",
        text="Paris is the capital and most populous city of France, situated along the Seine River.",
        source_id="geo_ref_02",
        provenance="TrustRAG-Demo-Corpus",
        metadata={"verified": True, "source_type": "encyclopedia", "domain": "wikipedia.org"},
    ),
    EvidenceDocument(
        doc_id="demo_aes_03",
        text="AES-256 uses a 256-bit symmetric cryptographic key and remains secure against practical brute-force attacks.",
        source_id="crypto_ref_03",
        provenance="TrustRAG-Demo-Corpus",
        metadata={"verified": True, "source_type": "official_docs", "domain": "nist.gov"},
    ),
    EvidenceDocument(
        doc_id="demo_paracetamol_04",
        text="Standard clinical guidelines state that the maximum safe daily dose of paracetamol for healthy adults is 4000 mg in 24 hours.",
        source_id="med_ref_04",
        provenance="TrustRAG-Demo-Corpus",
        metadata={"verified": True, "source_type": "peer_reviewed", "domain": "nih.gov"},
    ),
]


def _default_documents(corpus_path: str | Path | None = None) -> list[EvidenceDocument]:
    if corpus_path is not None and Path(corpus_path).is_file():
        docs: list[EvidenceDocument] = []
        with Path(corpus_path).open("r", encoding="utf-8") as fh:
            for idx, line in enumerate(fh):
                if len(docs) >= 100:
                    break
                if not line.strip():
                    continue
                rec = json.loads(line)
                doc = EvidenceDocument.from_record(rec, idx=idx)
                if doc is not None:
                    docs.append(doc)
        if docs:
            return docs
    default_boolq = Path("data/processed/boolq/validation.jsonl")
    if default_boolq.is_file():
        return _default_documents(default_boolq)
    return list(_DEFAULT_CORPUS)


def _check_dependencies() -> dict[str, bool]:
    pkgs = ("aiohttp", "pydantic", "scikit-learn", "numpy", "torch", "transformers", "peft", "trl", "datasets")
    mod_map = {"scikit-learn": "sklearn"}
    return {
        pkg: (importlib.util.find_spec(mod_map.get(pkg, pkg)) is not None)
        for pkg in pkgs
    }


def _to_evidence_docs(raw_docs: list[Any]) -> list[EvidenceDocument]:
    return [
        EvidenceDocument(
            doc_id=d.doc_id,
            text=d.text,
            source_id=d.source_id,
            provenance=d.provenance,
            metadata=dict(d.metadata),
        )
        for d in raw_docs
    ]


class AppRuntime:
    """Holds initialized TrustRAG backend service, monitoring, audit, and config state."""

    def __init__(
        self,
        *,
        service: TrustRAGService,
        audit_store: AuditLogStore,
        monitoring: MonitoringTracker,
        config_manager: RuntimeConfigManager,
        auth_token: str | None,
        environment: str,
        default_timeout_seconds: float,
        frontend_dir: Path | None,
    ) -> None:
        self.service = service
        self.audit = audit_store
        self.monitoring = monitoring
        self.config_manager = config_manager
        self.auth_token = auth_token
        self.environment = environment
        self.default_timeout_seconds = default_timeout_seconds
        self.frontend_dir = frontend_dir

    def sync_settings(self, updated: Settings) -> None:
        with self.service._lock:
            self.service.settings = updated.model_copy(deep=True)
            self.service._controller.settings = updated.model_copy(deep=True)


RUNTIME_KEY: web.AppKey[AppRuntime] = web.AppKey("runtime", AppRuntime)


async def _parse_json_body(request: web.Request, model_cls: Any) -> tuple[Any | None, web.Response | None]:
    try:
        raw = await request.json()
    except Exception:
        return None, json_error(400, error="Malformed JSON request body.", code="INVALID_JSON")
    try:
        return model_cls.model_validate(raw), None
    except ValidationError as exc:
        msgs = [f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in exc.errors()[:5]]
        return None, json_error(
            422,
            error="Request validation failed.",
            code="VALIDATION_ERROR",
            details=msgs,
        )


def create_app(
    *,
    service: TrustRAGService | None = None,
    corpus_path: str | Path | None = None,
    audit_log_path: str | Path | None = "logs/audit_events.jsonl",
    backup_dir: str | Path = "configs/backups",
    benchmark_report_path: str | Path = "reports/phase08_comprehensive_benchmark.json",
    frontend_dir: str | Path | None = "frontend",
    api_token: str | None = None,
    cors_origins: tuple[str, ...] = (),
    environment: str | None = None,
    rate_limit_max_requests: int = 120,
    default_timeout_seconds: float = 10.0,
) -> web.Application:
    """Create configured aiohttp Application wiring TrustRAGService and SPA frontend."""
    resolved_env = (environment or os.environ.get("TRUSTRAG_ENV") or "development").strip().lower()
    resolved_token = api_token if api_token is not None else (os.environ.get("TRUSTRAG_API_TOKEN") or None)
    if resolved_env == "production" and not resolved_token:
        raise RuntimeError(
            "TRUSTRAG_API_TOKEN must be configured when TRUSTRAG_ENV='production'."
        )

    env_cors = os.environ.get("TRUSTRAG_CORS_ORIGINS", "")
    resolved_cors = cors_origins or tuple(o.strip() for o in env_cors.split(",") if o.strip())

    cal_path = Path("configs/adaptive/temperature_calibrator_v1.json")
    if service is None:
        docs = _default_documents(corpus_path)
        svc = TrustRAGService(
            docs,
            settings=load_config(),
            calibrator_path=cal_path if cal_path.is_file() else None,
            default_timeout_seconds=default_timeout_seconds,
        )
    else:
        svc = service

    audit_store = AuditLogStore(log_path=audit_log_path)
    monitoring = MonitoringTracker(benchmark_report_path=benchmark_report_path)
    config_mgr = RuntimeConfigManager(
        svc.settings,
        audit_store=audit_store,
        backup_dir=backup_dir,
    )
    fdir = Path(frontend_dir) if frontend_dir is not None else None
    runtime = AppRuntime(
        service=svc,
        audit_store=audit_store,
        monitoring=monitoring,
        config_manager=config_mgr,
        auth_token=resolved_token,
        environment=resolved_env,
        default_timeout_seconds=default_timeout_seconds,
        frontend_dir=fdir if (fdir is not None and fdir.is_dir()) else None,
    )

    sec_mw = build_security_middleware(
        api_token=resolved_token,
        cors_origins=resolved_cors,
        rate_limiter=SlidingWindowRateLimiter(max_requests=rate_limit_max_requests, window_seconds=60.0),
        require_token_for_mutations=(resolved_env == "production"),
    )
    app = web.Application(middlewares=[sec_mw], client_max_size=1_048_576)
    app[RUNTIME_KEY] = runtime

    async def on_startup(_app: web.Application) -> None:
        await asyncio.to_thread(runtime.service.initialize)

    async def on_cleanup(_app: web.Application) -> None:
        await asyncio.to_thread(runtime.service.shutdown)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    # ---- Routes ----
    routes = web.RouteTableDef()

    @routes.get("/api/v1/health")
    async def get_health(_request: web.Request) -> web.Response:
        h = await asyncio.to_thread(runtime.service.health)
        srm_state = "fallback_deterministic"
        if h.srm_health is not None and h.srm_health.is_real_model:
            srm_state = "ready" if h.srm_health.available else "unavailable"
        payload = SystemHealthResponse(
            status=h.status,
            ready=h.ready,
            initialized=h.initialized,
            shut_down=h.shut_down,
            environment=runtime.environment,
            auth_mode="token_required" if runtime.auth_token else "local_dev_unauthenticated",
            corpus_documents=h.corpus_documents,
            adaptive_mode=h.adaptive_mode,
            calibration_active=h.calibration_active,
            calibration_version=h.calibration_version,
            components={
                "g1_guardrail": "active" if runtime.service.settings.guardrails.enabled else "disabled",
                "g2_msd": "active" if runtime.service.settings.msd.enabled else "disabled",
                "g3_verifier": "active" if runtime.service.settings.verification.enabled else "disabled",
                "retrieval": "ready" if h.corpus_documents > 0 else "empty",
                "srm": srm_state,
                "serving": h.status,
            },
            srm_backend_configured=h.srm_backend,
            srm_health=h.srm_health,
            dependencies=_check_dependencies(),
            total_requests=h.total_requests,
            error_requests=h.error_requests,
            timeout_requests=h.timeout_requests,
            peak_rss_mib=h.peak_rss_mib,
            timestamp=datetime.now(UTC).isoformat(),
        )
        return web.json_response(payload.model_dump())

    @routes.get("/api/v1/srm/health")
    async def get_srm_health(_request: web.Request) -> web.Response:
        h = await asyncio.to_thread(runtime.service.health)
        srm_h = h.srm_health
        return web.json_response(
            {
                "configured_backend": h.srm_backend,
                "active_backend": srm_h.backend_name if srm_h else "unknown",
                "is_fallback": not (srm_h.is_real_model if srm_h else False),
                "timeout_seconds": runtime.service.settings.srm.timeout_seconds,
                "health": srm_h.model_dump() if srm_h else None,
            }
        )

    @routes.post("/api/v1/g1/analyze")
    async def post_g1_analyze(request: web.Request) -> web.Response:
        body, err = await _parse_json_body(request, G1AnalyzeRequest)
        if err is not None:
            return err
        assert body is not None
        req_id = uuid.uuid4().hex[:12]
        t0 = time.perf_counter()

        def _run_g1() -> Any:
            cfg = runtime.service.settings.guardrails.model_copy(deep=True)
            if body.enable_paraphrasing is not None:
                cfg.enable_paraphrasing = body.enable_paraphrasing
                if cfg.enable_paraphrasing and cfg.paraphrase_backend == "disabled":
                    cfg.paraphrase_backend = "deterministic"
            return InputGuardrail(cfg).evaluate(body.query)

        assessment = await asyncio.wait_for(asyncio.to_thread(_run_g1), timeout=runtime.default_timeout_seconds)
        lat_ms = round((time.perf_counter() - t0) * 1000.0, 4)
        runtime.monitoring.record_g1_decision(assessment.decision.value, latency_ms=lat_ms)
        reason_vals = [rc.value for rc in assessment.reason_codes]
        match_cats = sorted({m.reason_code.value for m in assessment.matches})
        runtime.audit.record(
            request_id=req_id,
            event_category="G1_ANALYSIS",
            component="g1_guardrail",
            decision=assessment.decision.value,
            outcome=f"risk={assessment.risk_score:.4f}",
            explanation=assessment.explanation,
            evidence_refs=reason_vals,
        )
        resp = G1AnalyzeResponse(
            request_id=req_id,
            decision=assessment.decision.value,
            risk_score=assessment.risk_score,
            attack_categories=match_cats or reason_vals,
            flags=reason_vals,
            sanitized_query=assessment.normalized_input,
            paraphrased_query=assessment.paraphrased_query,
            paraphrase_accepted=assessment.paraphrase_accepted,
            paraphrase_rejection_reasons=list(assessment.paraphrase_rejection_reasons),
            explanation=assessment.explanation,
            latency_ms=lat_ms,
        )
        return web.json_response(resp.model_dump())

    @routes.post("/api/v1/g2/analyze")
    async def post_g2_analyze(request: web.Request) -> web.Response:
        body, err = await _parse_json_body(request, G2AnalyzeRequest)
        if err is not None:
            return err
        assert body is not None
        req_id = uuid.uuid4().hex[:12]
        t0 = time.perf_counter()

        def _run_g2() -> tuple[list[Any], list[str], list[str]]:
            docs = _to_evidence_docs(body.documents) if body.documents else list(runtime.service._documents)
            rels = [d.score for d in body.documents] if body.documents else None
            if body.documents is None and docs:
                det = MultiSignalDetector(
                    config=runtime.service.settings.msd,
                    calibrator=runtime.service._calibrator,
                )
                ret = TrustAwareRetriever(
                    documents=docs,
                    retrieval_config=runtime.service.settings.retrieval,
                    msd_config=runtime.service.settings.msd,
                    detector=det,
                ).retrieve_trusted(body.query, top_k=body.top_k)
                retained = [d.doc_id for d in ret.trusted_documents]
                filtered = [d.doc_id for d in ret.removed_documents]
                return list(ret.assessments), retained, filtered

            det = MultiSignalDetector(
                runtime.service.settings.msd,
                calibrator=runtime.service._calibrator,
            )
            assessments = det.assess_candidates(body.query, docs, rels)
            retained = [a.document_id for a in assessments if not a.removed_by_cap and a.decision.value != "POISONED"]
            filtered = [a.document_id for a in assessments if a.document_id not in retained]
            return assessments, retained, filtered

        assessments, retained_ids, filtered_ids = await asyncio.wait_for(
            asyncio.to_thread(_run_g2),
            timeout=runtime.default_timeout_seconds,
        )
        lat_ms = round((time.perf_counter() - t0) * 1000.0, 4)
        runtime.monitoring.record_g2_assessments([a.decision.value for a in assessments], latency_ms=lat_ms)
        runtime.audit.record(
            request_id=req_id,
            event_category="G2_MSD_ANALYSIS",
            component="g2_msd",
            decision=f"retained={len(retained_ids)},filtered={len(filtered_ids)}",
            outcome=f"assessed={len(assessments)}",
            explanation=f"Evaluated {len(assessments)} candidate documents for query.",
            evidence_refs=retained_ids[:10],
        )

        views: list[G2DocumentView] = []
        for a in assessments:
            sig_views = {
                k: SignalDetailView(
                    signal_id=v.signal_id,
                    signal_name=v.signal_name,
                    available=v.available,
                    value=v.value,
                    raw_value=v.raw_value,
                    z_score=v.z_score,
                    configured_weight=v.configured_weight,
                    effective_weight=v.effective_weight,
                    is_heuristic=v.is_heuristic,
                    status=v.status,
                    explanation=v.explanation,
                    flags=list(v.flags),
                )
                for k, v in a.signals.items()
            }
            snap = a.config_snapshot or {}
            views.append(
                G2DocumentView(
                    document_id=a.document_id,
                    source_id=a.source_id,
                    provenance=a.provenance,
                    trust_score=a.trust_score,
                    decision=a.decision.value,
                    original_retrieval_score=a.original_retrieval_score,
                    adjusted_retrieval_score=a.adjusted_retrieval_score,
                    removed_by_cap=a.removed_by_cap,
                    conflict_detected=a.conflict_detected,
                    conflicting_doc_ids=list(a.conflicting_doc_ids),
                    reason_codes=list(a.reason_codes),
                    calibration_active=bool(snap.get("calibration_active", False)),
                    calibration_version=snap.get("calibration_version"),
                    raw_trust_score=snap.get("raw_trust_score"),
                    signals=sig_views,
                )
            )

        cal = runtime.service._calibrator
        cal_ver = cal.artifact.version if (cal is not None and cal.artifact is not None) else None
        resp = G2AnalyzeResponse(
            request_id=req_id,
            query=body.query,
            candidate_count=len(views),
            retained_doc_ids=retained_ids,
            filtered_doc_ids=filtered_ids,
            removal_cap_ratio=runtime.service.settings.retrieval.removal_cap_ratio,
            calibration_active=bool(cal is not None and cal.is_active),
            calibration_version=cal_ver,
            assessments=views,
            latency_ms=lat_ms,
        )
        return web.json_response(resp.model_dump())

    @routes.post("/api/v1/g3/verify")
    async def post_g3_verify(request: web.Request) -> web.Response:
        body, err = await _parse_json_body(request, G3VerifyRequest)
        if err is not None:
            return err
        assert body is not None
        req_id = uuid.uuid4().hex[:12]
        t0 = time.perf_counter()

        def _run_g3() -> Any:
            docs = _to_evidence_docs(body.documents) if body.documents else list(runtime.service._documents)
            verifier = OutputEvidenceVerifier(runtime.service.settings.verification)
            return verifier.verify(body.answer, docs, query=body.query or None)

        rep = await asyncio.wait_for(asyncio.to_thread(_run_g3), timeout=runtime.default_timeout_seconds)
        lat_ms = round((time.perf_counter() - t0) * 1000.0, 4)
        verdict_val = rep.verdict.value if rep.verdict is not None else rep.overall_status.to_answer_verdict().value
        is_abstained = verdict_val in {"CONTRADICTED", "INSUFFICIENT_EVIDENCE"}
        runtime.monitoring.record_g3_verdict(
            verdict_val,
            abstained=is_abstained,
            latency_ms=lat_ms,
        )
        claim_views = [
            G3ClaimView(
                claim_id=c.claim_id,
                claim_text=c.claim_text,
                verdict=c.verdict.value if c.verdict is not None else c.outcome.to_claim_verdict().value,
                confidence=c.confidence,
                supporting_doc_ids=[ref.doc_id for ref in c.supporting_evidence_refs],
                contradicting_doc_ids=[ref.doc_id for ref in c.contradicting_evidence_refs],
                evidence_spans=[ref.matched_span for ref in (c.evidence_refs or c.supporting_evidence_refs or c.contradicting_evidence_refs)],
                explanation=c.explanation,
            )
            for c in rep.claims
        ]
        all_refs = sorted({did for c in claim_views for did in (c.supporting_doc_ids + c.contradicting_doc_ids)})
        runtime.audit.record(
            request_id=req_id,
            event_category="G3_VERIFICATION",
            component="g3_verifier",
            decision=verdict_val,
            outcome=f"claims={rep.total_claims},supported={rep.supported_count},contradicted={rep.contradicted_count}",
            explanation=rep.summary,
            evidence_refs=all_refs,
        )
        qc_reason = "; ".join(rep.query_consistency_reasons) if rep.query_consistency_reasons else None
        resp = G3VerifyResponse(
            request_id=req_id,
            overall_status=rep.overall_status.value,
            verdict=verdict_val,
            total_claims=rep.total_claims,
            supported_count=rep.supported_count,
            contradicted_count=rep.contradicted_count,
            insufficient_count=int(
                rep.insufficient_count if rep.insufficient_count is not None else rep.not_enough_evidence_count
            ),
            uncertain_count=rep.uncertain_count,
            abstained=is_abstained,
            query_consistent=rep.query_consistent,
            query_consistency_reason=qc_reason,
            claims=claim_views,
            latency_ms=lat_ms,
        )
        return web.json_response(resp.model_dump())

    @routes.post("/api/v1/evidence/retrieve")
    async def post_evidence_retrieve(request: web.Request) -> web.Response:
        body, err = await _parse_json_body(request, RetrievalEvidenceRequest)
        if err is not None:
            return err
        assert body is not None
        req_id = uuid.uuid4().hex[:12]

        def _run_ret() -> tuple[int, list[EvidenceDocument]]:
            docs = list(runtime.service._documents)
            if not docs:
                return 0, []
            det = MultiSignalDetector(
                config=runtime.service.settings.msd,
                calibrator=runtime.service._calibrator,
            )
            ret = TrustAwareRetriever(
                documents=docs,
                retrieval_config=runtime.service.settings.retrieval,
                msd_config=runtime.service.settings.msd,
                detector=det,
            ).retrieve_trusted(body.query, top_k=body.top_k)
            return len(docs), list(ret.trusted_documents)

        corpus_sz, returned_docs = await asyncio.wait_for(
            asyncio.to_thread(_run_ret),
            timeout=runtime.default_timeout_seconds,
        )
        items = [
            EvidenceItemView(
                doc_id=d.doc_id,
                provenance=d.provenance or "unknown",
                source_id=d.source_id or "",
                text_preview=(d.text[:240] + "...") if len(d.text) > 240 else d.text,
                metadata=dict(d.metadata),
            )
            for d in returned_docs
        ]
        return web.json_response(
            RetrievalEvidenceResponse(
                request_id=req_id,
                query=body.query,
                corpus_size=corpus_sz,
                returned_count=len(items),
                items=items,
            ).model_dump()
        )

    @routes.post("/api/v1/pipeline/execute")
    async def post_pipeline_execute(request: web.Request) -> web.Response:
        body, err = await _parse_json_body(request, PipelineExecuteRequest)
        if err is not None:
            return err
        assert body is not None
        req_id = uuid.uuid4().hex[:12]
        eff_timeout = body.request_timeout_seconds or runtime.default_timeout_seconds
        svc_req = ProductionQueryRequest(
            request_id=req_id,
            query=body.query,
            top_k=body.top_k,
            request_timeout_seconds=eff_timeout,
        )
        try:
            out = await asyncio.wait_for(
                asyncio.to_thread(runtime.service.handle_query, svc_req),
                timeout=eff_timeout + 1.0,
            )
        except TimeoutError:
            runtime.monitoring.record_pipeline_outcome(
                latency_ms=eff_timeout * 1000.0,
                status="ERROR",
                abstained=True,
                is_timeout=True,
            )
            return json_error(
                504,
                error="Pipeline execution timed out.",
                code="REQUEST_TIMEOUT",
                request_id=req_id,
            )

        runtime.monitoring.record_pipeline_outcome(
            latency_ms=out.latency_ms,
            status=out.status,
            g1_decision=out.g1_decision,
            g3_verdict=out.g3_verdict,
            blocked=out.blocked_by_guardrail,
            abstained=out.abstained,
            is_timeout=("REQUEST_TIMEOUT" in out.fail_safe_events),
        )
        runtime.audit.record(
            request_id=out.request_id,
            event_category="PIPELINE_EXECUTION",
            component="pipeline",
            decision=out.status,
            outcome=f"g1={out.g1_decision},g3={out.g3_verdict},abstained={out.abstained}",
            explanation=f"Pipeline finished in {out.latency_ms}ms.",
            evidence_refs=list(out.retained_doc_ids),
        )
        resp = PipelineExecuteResponse.model_validate(out.model_dump())
        return web.json_response(resp.model_dump(), status=503 if out.status == "ERROR" else 200)

    @routes.get("/api/v1/monitoring/metrics")
    async def get_monitoring_metrics(_request: web.Request) -> web.Response:
        snap = await asyncio.to_thread(runtime.monitoring.snapshot)
        return web.json_response(snap.model_dump())

    @routes.get("/api/v1/config")
    async def get_config(_request: web.Request) -> web.Response:
        snap = await asyncio.to_thread(runtime.config_manager.snapshot)
        return web.json_response(snap.model_dump())

    @routes.post("/api/v1/config/validate")
    async def post_config_validate(request: web.Request) -> web.Response:
        body, err = await _parse_json_body(request, ConfigUpdateRequest)
        if err is not None:
            return err
        assert body is not None
        valid, diffs, errors = runtime.config_manager.validate_changes(body.changes)
        return web.json_response(
            {
                "valid": valid,
                "applied": False,
                "requires_confirmation": True,
                "restart_required": any(d.restart_required for d in diffs),
                "diffs": [d.model_dump() for d in diffs],
                "errors": errors,
            },
            status=200 if valid else 422,
        )

    @routes.post("/api/v1/config/apply")
    async def post_config_apply(request: web.Request) -> web.Response:
        body, err = await _parse_json_body(request, ConfigUpdateRequest)
        if err is not None:
            return err
        assert body is not None
        req_id = uuid.uuid4().hex[:12]
        res = runtime.config_manager.apply_changes(
            body,
            request_id=req_id,
            on_apply=runtime.sync_settings,
        )
        status_code = 200 if res.valid else 422
        return web.json_response(res.model_dump(), status=status_code)

    @routes.post("/api/v1/config/restore")
    async def post_config_restore(request: web.Request) -> web.Response:
        try:
            raw = await request.json()
        except Exception:
            raw = {}
        confirm = bool(raw.get("confirm", False)) if isinstance(raw, dict) else False
        actor = str(raw.get("actor", "operator"))[:64] if isinstance(raw, dict) else "operator"
        res = runtime.config_manager.restore_defaults(
            confirm=confirm,
            actor=actor,
            request_id=uuid.uuid4().hex[:12],
            on_apply=runtime.sync_settings,
        )
        return web.json_response(res.model_dump())

    @routes.get("/api/v1/audit/logs")
    async def get_audit_logs(request: web.Request) -> web.Response:
        q = request.query
        try:
            page = int(q.get("page", "1"))
            page_size = int(q.get("page_size", "50"))
        except ValueError:
            return json_error(422, error="Invalid pagination parameters.", code="VALIDATION_ERROR")
        res = runtime.audit.query(
            event_type=q.get("event_type"),
            component=q.get("component"),
            request_id=q.get("request_id"),
            since=q.get("since"),
            until=q.get("until"),
            page=page,
            page_size=page_size,
        )
        return web.json_response(res.model_dump())

    @routes.get("/openapi.json")
    async def get_openapi(_request: web.Request) -> web.Response:
        return web.json_response(generate_openapi_spec())

    @routes.get("/docs")
    async def get_docs(_request: web.Request) -> web.Response:
        spec = generate_openapi_spec()
        paths_html = "".join(
            f"<li><code>{next(iter(methods.keys())).upper()} {path}</code> — {next(iter(methods.values())).get('summary', '')}</li>"
            for path, methods in spec["paths"].items()
        )
        html = (
            "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<title>TrustRAG API Docs</title></head>"
            "<body><h1>TrustRAG Operational API (OpenAPI 3.1)</h1>"
            "<p><a href='/openapi.json'>Download OpenAPI JSON</a></p>"
            f"<ul>{paths_html}</ul></body></html>"
        )
        return web.Response(text=html, content_type="text/html")

    # ---- Frontend SPA Static Serving (traversal-safe) ----
    @routes.get("/")
    async def get_index(_request: web.Request) -> web.StreamResponse:
        if runtime.frontend_dir is None or not (runtime.frontend_dir / "index.html").is_file():
            return web.Response(text="TrustRAG API running. Frontend assets not mounted.", content_type="text/plain")
        return web.FileResponse(runtime.frontend_dir / "index.html")

    @routes.get("/{asset_path:.*}")
    async def get_static_asset(request: web.Request) -> web.StreamResponse:
        if runtime.frontend_dir is None:
            return json_error(404, error="Not found.", code="NOT_FOUND")
        rel = request.match_info["asset_path"]
        if rel.startswith("api/"):
            return json_error(404, error="API route not found.", code="NOT_FOUND")
        base_resolved = runtime.frontend_dir.resolve()
        candidate = (base_resolved / rel).resolve()
        if not str(candidate).startswith(str(base_resolved)) or not candidate.is_file():
            if (base_resolved / "index.html").is_file() and "." not in Path(rel).name:
                return web.FileResponse(base_resolved / "index.html")
            return json_error(404, error="Asset not found.", code="NOT_FOUND")
        return web.FileResponse(candidate)

    app.add_routes(routes)
    return app
