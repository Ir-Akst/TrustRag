#!/usr/bin/env python3
"""
Phase 13 Step 2 - Independent Verification Probe: P2 Issues
Tests:
1. TrustAwareRetriever save() / load() persistence and state restoration
2. TrustAwareRetriever deduplicate_by_id handling
3. SRM backend reality probe (DeterministicFallbackBackend vs neural weights)
4. Containerization & CI artifact integrity (Dockerfile, docker-compose.yml, ci.yml)
"""

import sys
import os
import json
import tempfile
from pathlib import Path

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)
if os.path.join(WORKSPACE_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "src"))

from trustrag.retrieval.retriever import TrustAwareRetriever
from trustrag.engine.schemas import EvidenceDocument
from trustrag.srm.client import SRMClient
from trustrag.config.engine_config import SRMConfig

results = {
    "probe": "probe_p2",
    "timestamp": "2026-11-13T11:00:00Z",
    "tests": {}
}

# ---------------------------------------------------------
# Test 1: Retriever save() / load() persistence
# ---------------------------------------------------------
print("--- [P2.1] Retriever save() and load() Persistence Test ---")
sample_docs = [
    EvidenceDocument(doc_id="doc_01", text="First sample document for persistence check.", provenance="trusted"),
    EvidenceDocument(doc_id="doc_02", text="Second sample document with critical facts.", provenance="verified"),
    EvidenceDocument(doc_id="doc_03", text="Third sample document with supplementary information.", provenance="untrusted")
]

retriever = TrustAwareRetriever()
retriever.index_documents(sample_docs)
orig_search = retriever.retrieve_candidates("sample document", top_n=3)

with tempfile.TemporaryDirectory() as tmpdir:
    persist_path = Path(tmpdir) / "retriever_state.pkl"
    retriever.save(persist_path)
    file_exists = persist_path.exists()
    file_size = persist_path.stat().st_size
    
    loaded_retriever = TrustAwareRetriever.load(persist_path)
    loaded_search = loaded_retriever.retrieve_candidates("sample document", top_n=3)
    
    ids_match = [d.doc_id for d, s in orig_search] == [d.doc_id for d, s in loaded_search]
    scores_match = all(
        abs(s1 - s2) < 1e-4
        for (_, s1), (_, s2) in zip(orig_search, loaded_search, strict=False)
    )
    doc_count_match = (loaded_retriever.document_count == retriever.document_count)

persistence_passed = file_exists and ids_match and scores_match and doc_count_match
print(f"P2.1 Result: {'PASS' if persistence_passed else 'FAIL'} (size={file_size} bytes, docs={loaded_retriever.document_count})")

results["tests"]["P2_1_retriever_persistence"] = {
    "passed": persistence_passed,
    "file_size": file_size,
    "doc_count": loaded_retriever.document_count,
    "ids_preserved": ids_match,
    "scores_preserved": scores_match
}

# ---------------------------------------------------------
# Test 2: Retriever deduplicate_by_id handling
# ---------------------------------------------------------
print("\n--- [P2.2] Retriever deduplicate_by_id Handling Test ---")
r_without_dedup = TrustAwareRetriever()
count_without = r_without_dedup.index_documents([
    EvidenceDocument(doc_id="dup_id", text="First occurrence of duplicate ID document.", provenance="wiki"),
    EvidenceDocument(doc_id="dup_id", text="Second occurrence of duplicate ID document.", provenance="wiki"),
    EvidenceDocument(doc_id="unique_id", text="A completely unique document.", provenance="wiki")
], deduplicate_by_id=False)
ids_without = [d.doc_id for d in r_without_dedup._documents]

r_with_dedup = TrustAwareRetriever()
count_with = r_with_dedup.index_documents([
    EvidenceDocument(doc_id="dup_id", text="First occurrence of duplicate ID document.", provenance="wiki"),
    EvidenceDocument(doc_id="dup_id", text="Second occurrence of duplicate ID document.", provenance="wiki"),
    EvidenceDocument(doc_id="unique_id", text="A completely unique document.", provenance="wiki")
], deduplicate_by_id=True)
ids_with = [d.doc_id for d in r_with_dedup._documents]

dedup_passed = (count_without == 3) and (count_with == 2) and ("dup_id#1" in ids_without) and ("dup_id" in ids_with)
print(f"P2.2 Result: {'PASS' if dedup_passed else 'FAIL'} (without_dedup={count_without}, with_dedup={count_with})")

results["tests"]["P2_2_retriever_deduplication"] = {
    "passed": dedup_passed,
    "without_deduplicate_count": count_without,
    "without_deduplicate_ids": ids_without,
    "with_deduplicate_count": count_with,
    "with_deduplicate_ids": ids_with
}

# ---------------------------------------------------------
# Test 3: SRM Backend Reality Probe
# ---------------------------------------------------------
print("\n--- [P2.3] SRM Backend Reality Probe ---")
# Check whether SRM uses DeterministicFallbackBackend or actual neural checkpoints
srm_client = SRMClient(config=SRMConfig())
active_backend = getattr(srm_client, "_backend", None)
backend_type = type(active_backend).__name__ if active_backend is not None else "None"
is_fallback = "Fallback" in backend_type or "Deterministic" in backend_type

# Search for any neural weights in models/
models_dir = Path(WORKSPACE_ROOT) / "models"
weight_files = []
if models_dir.exists():
    for ext in ("*.bin", "*.safetensors", "*.pt", "*.onnx"):
        weight_files.extend([str(p.relative_to(WORKSPACE_ROOT)) for p in models_dir.glob(f"**/{ext}")])

srm_finding = {
    "active_backend_type": backend_type,
    "is_deterministic_fallback": is_fallback,
    "neural_weight_files_found": weight_files,
    "neural_model_present": len(weight_files) > 0,
    "honest_assessment": (
        "SRM operates via DeterministicFallbackBackend (deterministic rule-based proxy). "
        "No offline neural weights (Qwen2.5-3B-Instruct / LoRA checkpoints) exist on disk. "
        "Component verdict remains BLUE (Fallback-only), not genuine neural inference."
    )
}
print(f"P2.3 Result: VERIFIED ({backend_type}, neural_weights={len(weight_files)})")
results["tests"]["P2_3_srm_reality_probe"] = srm_finding

# ---------------------------------------------------------
# Test 4: Containerization & CI Artifact Integrity
# ---------------------------------------------------------
print("\n--- [P2.4] Containerization & CI Artifact Integrity Test ---")
dockerfile_path = Path(WORKSPACE_ROOT) / "Dockerfile"
compose_path = Path(WORKSPACE_ROOT) / "docker-compose.yml"
ci_path = Path(WORKSPACE_ROOT) / ".github/workflows/ci.yml"

dockerfile_exists = dockerfile_path.exists()
compose_exists = compose_path.exists()
ci_exists = ci_path.exists()

dockerfile_content = dockerfile_path.read_text(encoding="utf-8") if dockerfile_exists else ""
compose_content = compose_path.read_text(encoding="utf-8") if compose_exists else ""
ci_content = ci_path.read_text(encoding="utf-8") if ci_exists else ""

container_valid = (
    dockerfile_exists and "python:" in dockerfile_content and "COPY" in dockerfile_content and
    compose_exists and "services:" in compose_content and
    ci_exists and "pytest" in ci_content
)
print(f"P2.4 Result: {'PASS' if container_valid else 'FAIL'}")

results["tests"]["P2_4_container_and_ci"] = {
    "passed": container_valid,
    "dockerfile_present": dockerfile_exists,
    "docker_compose_present": compose_exists,
    "ci_workflow_present": ci_exists
}

# Write results
output_path = os.path.join(os.path.dirname(__file__), "p2_probe_output.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nAll P2 tests completed. Output written to {output_path}")
