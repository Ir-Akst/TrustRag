"""
Validator A: Schema Validation for G3 Claim Graphs and Evidence Graphs.
Validates structural closedness, entity/predicate/quantity typing,
active/passive voice constraints, unknown-agent representations,
and rejects dangling edges and malformed graph structures.
"""

import json
import os
import sys
from typing import Dict, Any, List, Tuple


class SchemaValidator:
    ALLOWED_NODE_TYPES = {"entity", "predicate", "quantity", "temporal", "condition", "modifier"}
    ALLOWED_RELATIONS = {
        "subject_of", "object_of", "agent_of", "patient_of",
        "quantifies", "temporally_bounds", "conditions", "modifies", "coordinates_with"
    }

    def __init__(self, fixtures_dir: str):
        self.fixtures_dir = fixtures_dir

    def validate_claim_graph(self, graph: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        # Required top-level keys
        for key in ["graph_id", "claim_text", "nodes", "edges", "is_passive", "unknown_agent"]:
            if key not in graph:
                errors.append(f"Missing required key: {key}")

        if errors:
            return False, errors

        claim_text = graph["claim_text"]
        if not isinstance(claim_text, str) or not claim_text.strip():
            errors.append("claim_text must be non-empty string")

        nodes = graph.get("nodes", [])
        if not isinstance(nodes, list) or len(nodes) == 0:
            errors.append("nodes must be a non-empty list")
            return False, errors

        node_map = {}
        quantities = []
        has_predicate = False
        has_agent_or_patient = False

        for idx, node in enumerate(nodes):
            if not isinstance(node, dict):
                errors.append(f"Node at index {idx} must be a dictionary")
                continue
            for rk in ["node_id", "node_type", "text"]:
                if rk not in node:
                    errors.append(f"Node {idx} missing required key: {rk}")

            nid = node.get("node_id")
            ntype = node.get("node_type")
            if nid in node_map:
                errors.append(f"Duplicate node_id: {nid}")
            node_map[nid] = node

            if ntype not in self.ALLOWED_NODE_TYPES:
                errors.append(f"Node {nid} has invalid node_type: {ntype}")
            if ntype == "predicate":
                has_predicate = True
            if ntype == "quantity":
                quantities.append(nid)

        if not has_predicate:
            errors.append("Claim graph must contain at least one predicate node")

        # Edge validation
        edges = graph.get("edges", [])
        if not isinstance(edges, list):
            errors.append("edges must be a list")
            return False, errors

        edge_map = {}
        quantity_quantifies = set()
        has_agent = False
        has_patient = False

        for idx, edge in enumerate(edges):
            if not isinstance(edge, dict):
                errors.append(f"Edge {idx} must be a dictionary")
                continue
            for rk in ["edge_id", "source_id", "target_id", "relation"]:
                if rk not in edge:
                    errors.append(f"Edge {idx} missing required key: {rk}")

            eid = edge.get("edge_id")
            src = edge.get("source_id")
            tgt = edge.get("target_id")
            rel = edge.get("relation")

            if eid in edge_map:
                errors.append(f"Duplicate edge_id: {eid}")
            edge_map[eid] = edge

            # Dangling reference checks
            if src not in node_map:
                errors.append(f"Edge {eid} has dangling source_id: {src}")
            if tgt not in node_map:
                errors.append(f"Edge {eid} has dangling target_id: {tgt}")

            if rel not in self.ALLOWED_RELATIONS:
                errors.append(f"Edge {eid} has invalid relation: {rel}")

            if rel == "quantifies":
                quantity_quantifies.add(src)
                # target must be entity or predicate
                if tgt in node_map and node_map[tgt].get("node_type") not in ("entity", "predicate"):
                    errors.append(f"Quantifies edge target must be entity or predicate, got {node_map[tgt].get('node_type')}")

            if rel in ("agent_of", "subject_of"):
                has_agent = True
            if rel in ("patient_of", "object_of"):
                has_patient = True

        # Quantity constraint: each quantity must quantify an entity or predicate
        for qid in quantities:
            if qid not in quantity_quantifies:
                errors.append(f"Quantity node {qid} must have a quantifies edge to an entity or predicate")

        # Voice constraints
        is_passive = graph.get("is_passive", False)
        unknown_agent = graph.get("unknown_agent", False)

        if is_passive:
            if not has_patient:
                errors.append("Passive construction requires patient_of edge")
            if unknown_agent:
                # Must have an unknown agent entity node
                unknown_nodes = [nid for nid, n in node_map.items() if n.get("is_unknown") is True]
                if not unknown_nodes:
                    errors.append("Passive claim with unknown_agent=true must declare an unknown entity node")
        else:
            if not has_agent:
                errors.append("Active construction requires agent_of or subject_of edge")

        return len(errors) == 0, errors

    def validate_evidence_graph(self, graph: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        for key in ["graph_id", "evidence_id", "document_id", "passage_text", "provenance", "nodes", "edges"]:
            if key not in graph:
                errors.append(f"Missing required key: {key}")

        if errors:
            return False, errors

        prov = graph.get("provenance", {})
        for pk in ["source", "timestamp", "trust_level", "signature_verified"]:
            if pk not in prov:
                errors.append(f"Evidence provenance missing {pk}")

        nodes = graph.get("nodes", [])
        node_map = {n.get("node_id"): n for n in nodes if isinstance(n, dict)}
        edges = graph.get("edges", [])

        for edge in edges:
            src = edge.get("source_id")
            tgt = edge.get("target_id")
            if src not in node_map:
                errors.append(f"Dangling source edge in evidence: {src}")
            if tgt not in node_map:
                errors.append(f"Dangling target edge in evidence: {tgt}")

        return len(errors) == 0, errors

    def run(self) -> Dict[str, Any]:
        valid_claims_path = os.path.join(self.fixtures_dir, "valid_claim_graphs.json")
        invalid_claims_path = os.path.join(self.fixtures_dir, "invalid_claim_graphs.json")
        valid_evd_path = os.path.join(self.fixtures_dir, "valid_evidence_graphs.json")
        invalid_evd_path = os.path.join(self.fixtures_dir, "invalid_evidence_graphs.json")

        with open(valid_claims_path, "r", encoding="utf-8") as f:
            valid_claims = json.load(f)
        with open(invalid_claims_path, "r", encoding="utf-8") as f:
            invalid_claims = json.load(f)
        with open(valid_evd_path, "r", encoding="utf-8") as f:
            valid_evds = json.load(f)
        with open(invalid_evd_path, "r", encoding="utf-8") as f:
            invalid_evds = json.load(f)

        results = {
            "valid_claims_tested": len(valid_claims),
            "valid_claims_passed": 0,
            "invalid_claims_tested": len(invalid_claims),
            "invalid_claims_rejected": 0,
            "valid_evd_tested": len(valid_evds),
            "valid_evd_passed": 0,
            "invalid_evd_tested": len(invalid_evds),
            "invalid_evd_rejected": 0,
            "status": "PASS"
        }

        for vc in valid_claims:
            ok, errs = self.validate_claim_graph(vc)
            if ok:
                results["valid_claims_passed"] += 1
            else:
                results["status"] = "FAIL"
                results.setdefault("failures", []).append({"id": vc.get("graph_id"), "errors": errs})

        for ic in invalid_claims:
            ok, errs = self.validate_claim_graph(ic["data"])
            if not ok:
                results["invalid_claims_rejected"] += 1
            else:
                results["status"] = "FAIL"
                results.setdefault("failures", []).append({"id": ic["id"], "expected_error": ic["expected_error"]})

        for ve in valid_evds:
            ok, errs = self.validate_evidence_graph(ve)
            if ok:
                results["valid_evd_passed"] += 1
            else:
                results["status"] = "FAIL"
                results.setdefault("failures", []).append({"id": ve.get("graph_id"), "errors": errs})

        for ie in invalid_evds:
            ok, errs = self.validate_evidence_graph(ie["data"])
            if not ok:
                results["invalid_evd_rejected"] += 1
            else:
                results["status"] = "FAIL"
                results.setdefault("failures", []).append({"id": ie["id"], "expected_error": ie["expected_error"]})

        return results


if __name__ == "__main__":
    fixtures = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))
    validator = SchemaValidator(fixtures)
    res = validator.run()
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["status"] == "PASS" else 1)

