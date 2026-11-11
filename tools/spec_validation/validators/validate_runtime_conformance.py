"""
Validator J: Live Codebase Conformance & Benchmark Validator.
Directly exercises the real production TrustRAG modules (src/trustrag/) against:
- Canonical Unicode fixtures (unicode_test_cases.json) via detect_obfuscation & MultiSignalDetector
- Historical G3 regression probes (historical_regression_cases.json) via OutputEvidenceVerifier
- Stage 7 Generated-Answer Unicode Inspection via TrustRAGPipeline
- Honest cold-start, warm-start (p50, p95, p99), and peak memory measurements of OutputEvidenceVerifier
"""

import json
import logging
import os
import statistics
import sys
import time
import tracemalloc
from typing import Dict, Any, List


class RuntimeConformanceValidator:
    def __init__(self, repo_root: str, fixtures_dir: str):
        self.repo_root = repo_root
        self.fixtures_dir = fixtures_dir
        src_path = os.path.join(repo_root, "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

    def run(self) -> Dict[str, Any]:
        logging.disable(logging.CRITICAL)
        tracemalloc.start()
        t_import0 = time.perf_counter()

        from trustrag.data.taxonomy import DocumentSecurityLabel
        from trustrag.detection.msd import MultiSignalDetector
        from trustrag.engine.schemas import EvidenceDocument, G3AnswerVerdict
        from trustrag.engine.text_utils import detect_obfuscation
        from trustrag.pipeline.trustrag_pipeline import TrustRAGPipeline
        from trustrag.verification.output_verifier import OutputEvidenceVerifier

        det = MultiSignalDetector()
        verifier = OutputEvidenceVerifier()
        cold_init_ms = (time.perf_counter() - t_import0) * 1000.0

        # 1. Real Unicode policy checks
        uni_path = os.path.join(self.fixtures_dir, "unicode_test_cases.json")
        with open(uni_path, "r", encoding="utf-8") as f:
            uni_cases = json.load(f)

        ref_doc = EvidenceDocument(doc_id="ref_clean", text="Aspirin reduces fever safely in adults at 500 mg daily.")
        uni_failures = []
        # Query contains clean domain words matching the attack payloads so Retrieval indexes & tests G2/Stage 5
        probe_query = "previous instructions administer clinical dose safety checks hidden override system prompt"
        for tc in uni_cases:
            tid = tc["test_id"]
            text = tc["original_text"]
            doc = EvidenceDocument(doc_id=tid, text=text)
            a = det.assess_candidates(probe_query, [doc, ref_doc])[0]
            q = "aspirin safety fever" if tc["expected_decision"] == "CLEAN" else probe_query
            pipe_resp = TrustRAGPipeline(documents=[doc]).run(q, top_k=1)

            if tc["expected_decision"] == "CLEAN":
                has_obf, _, _ = detect_obfuscation(text)
                if has_obf or a.decision != DocumentSecurityLabel.CLEAN or pipe_resp.unsafe_output_quarantined:
                    uni_failures.append({"test_id": tid, "reason": f"Expected CLEAN/ALLOW, got G2={a.decision.value}, quarantined={pipe_resp.unsafe_output_quarantined}"})
            else:
                # Attack payloads must be flagged by G2 (POISONED or security UNCERTAIN) AND blocked from downstream display/evidence
                is_g2_flagged = a.decision == DocumentSecurityLabel.POISONED or (
                    a.decision == DocumentSecurityLabel.UNCERTAIN and "DOC_OBFUSCATION" in a.reason_codes
                )
                exposed = any(d.doc_id == tid for d in pipe_resp.evidence)
                # Note: if unretrieved (candidate_count==0), doc never reached Gen/G3/SRM and safe_to_display is False
                # If retrieved with top_k=1, removal_cap==0 so Stage 5 quarantines it (unsafe_output_quarantined==True)
                cand_count = pipe_resp.trust_report.retrieval_summary.get("candidate_count", 0)
                if not is_g2_flagged or exposed or pipe_resp.safe_to_display or (cand_count > 0 and not pipe_resp.unsafe_output_quarantined):
                    uni_failures.append({
                        "test_id": tid,
                        "reason": f"Security failure: G2={a.decision.value}, reasons={a.reason_codes}, cand={cand_count}, quarantined={pipe_resp.unsafe_output_quarantined}, exposed={exposed}",
                    })

        # 2. Real G3 historical regression fixture checks
        hist_path = os.path.join(self.fixtures_dir, "historical_regression_cases.json")
        with open(hist_path, "r", encoding="utf-8") as f:
            hist_cases = json.load(f)

        hist_failures = []
        g3_checked = 0
        for hc in hist_cases:
            exp = hc["expected_verdict"]
            if exp not in ("SUPPORTED", "NOT_SUPPORTED"):
                continue
            g3_checked += 1
            res = verifier.verify(hc["claim"], [EvidenceDocument(doc_id="ev1", text=hc["evidence"])])
            if exp == "SUPPORTED" and res.verdict != G3AnswerVerdict.SUPPORTED:
                hist_failures.append({"case_id": hc["case_id"], "expected": exp, "got": res.verdict.value})
            elif exp == "NOT_SUPPORTED" and res.verdict == G3AnswerVerdict.SUPPORTED:
                hist_failures.append({"case_id": hc["case_id"], "expected": exp, "got": res.verdict.value})

        # 3. Stage 7 Generated-Answer Unicode Inspection check
        p_stage7 = TrustRAGPipeline(documents=[ref_doc]).run(
            "aspirin fever",
            top_k=1,
            answer_override="Aspirin re\u200bduces fever safely in adults at 500 mg daily.",
        )
        stage7_ok = (
            p_stage7.trust_report.overall_trust_decision == "FLAGGED"
            and p_stage7.unsafe_output_quarantined is True
            and p_stage7.safe_to_display is False
            and any(t.startswith("ANSWER_UNICODE:FLAGGED") for t in p_stage7.trust_report.execution_trace)
        )

        # 4. Honest Performance Profile of OutputEvidenceVerifier (5 warmup + 100 warm runs)
        sample_ev = EvidenceDocument(doc_id="perf1", text="Aspirin reduces severe fever in adult patients at 500 mg daily.")
        sample_claim = "Aspirin reduces severe fever in adult patients at 500 mg daily."
        lats: List[float] = []
        for _ in range(105):
            t0 = time.perf_counter()
            verifier.verify(sample_claim, [sample_ev])
            lats.append((time.perf_counter() - t0) * 1000.0)

        warm = sorted(lats[5:])
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mib = round(peak_bytes / (1024.0 * 1024.0), 3)

        status = "PASS" if not uni_failures and not hist_failures and stage7_ok else "FAIL"
        return {
            "status": status,
            "unicode_cases_checked": len(uni_cases),
            "unicode_failures": uni_failures,
            "historical_g3_checked": g3_checked,
            "historical_g3_failures": hist_failures,
            "stage7_answer_unicode_ok": stage7_ok,
            "verifier_performance": {
                "scope": "Heuristic/TF-IDF OutputEvidenceVerifier (no external ML/NLI model loaded)",
                "cold_import_init_ms": round(cold_init_ms, 2),
                "warm_p50_ms": round(warm[49], 3),
                "warm_p95_ms": round(warm[94], 3),
                "warm_p99_ms": round(warm[98], 3),
                "warm_mean_ms": round(statistics.mean(warm), 3),
                "peak_traced_heap_mib": peak_mib,
            },
        }


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    repo_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))
    fixtures = os.path.join(base_dir, "fixtures")
    val = RuntimeConformanceValidator(repo_dir, fixtures)
    out = val.run()
    print(json.dumps(out, indent=2))
    sys.exit(0 if out["status"] == "PASS" else 1)

