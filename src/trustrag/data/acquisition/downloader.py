"""Reliable dataset download, integrity verification, and ingestion pipeline for TrustRAG.

Provides deterministic, resumable acquisition for canonical research datasets:
- RAGTruth (ParticleMedia/RAGTruth)
- HaluEval (RUCAIBox/HaluEval & pminervini/HaluEval)
- HotpotQA (hotpotqa/hotpot_qa)
- MS MARCO (microsoft/ms_marco)
- Natural Questions (google-research-datasets/natural_questions)
- LLM-AggreFact (gated access diagnostics)
- RSB (local import interface diagnostics)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from trustrag.data.exceptions import AcquisitionError, ValidationError

logger = logging.getLogger(__name__)

# Canonical Official Remote Sources
CANONICAL_SOURCES: Dict[str, Dict[str, Any]] = {
    "ragtruth": {
        "repo": "https://github.com/ParticleMedia/RAGTruth",
        "response_url": "https://raw.githubusercontent.com/ParticleMedia/RAGTruth/main/dataset/response.jsonl",
        "source_info_url": "https://raw.githubusercontent.com/ParticleMedia/RAGTruth/main/dataset/source_info.jsonl",
        "license": "MIT",
        "version": "1.0",
        "expected_records": 17790,
    },
    "halueval": {
        "repo": "https://github.com/RUCAIBox/HaluEval",
        "qa_url": "https://raw.githubusercontent.com/RUCAIBox/HaluEval/main/data/qa_data.json",
        "license": "MIT",
        "version": "1.0",
        "expected_records": 10000,
    },
    "hotpotqa": {
        "hf_repo": "hotpotqa/hotpot_qa",
        "config": "distractor",
        "parquet_url": "https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/main/distractor/validation-00000-of-00001.parquet",
        "license": "CC-BY-SA-4.0",
        "version": "1.0",
        "expected_records": 7405,
    },
    "ms_marco": {
        "hf_repo": "microsoft/ms_marco",
        "config": "v1.1",
        "parquet_url": "https://huggingface.co/datasets/microsoft/ms_marco/resolve/main/v1.1/validation-00000-of-00001.parquet",
        "license": "Microsoft Research License / CC-BY-4.0",
        "version": "1.1",
        "expected_records": 10047,
    },
    "natural_questions": {
        "hf_repo": "google-research-datasets/natural_questions",
        "config": "default",
        "license": "CC-BY-SA-3.0",
        "version": "1.0",
        "expected_records": 7830,
    },
    "llm_aggrefact": {
        "hf_repo": "lytang/LLM-AggreFact",
        "license": "CC-BY-ND-4.0",
        "access": "GATED",
        "url": "https://huggingface.co/datasets/lytang/LLM-AggreFact",
    },
    "rsb": {
        "paper": "arXiv:2505.18543",
        "access": "LOCAL_IMPORT_ONLY",
        "license": "Pending Verification",
    },
}


def compute_file_sha256(file_path: Union[str, Path], chunk_size: int = 65536) -> str:
    """Compute cryptographic SHA-256 digest of a local file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha.update(chunk)
    return sha.hexdigest()


@dataclass
class DatasetArtifactEntry:
    """Metadata describing a single downloaded or processed dataset artifact."""

    file_name: str
    relative_path: str
    file_size_bytes: int
    sha256: str
    record_count: int
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class DatasetManifest:
    """Manifest recording provenance, checksums, and records of an acquired dataset."""

    dataset_name: str
    version: str
    license: str
    source_uri: str
    status: str
    download_timestamp: str
    raw_artifacts: List[DatasetArtifactEntry] = field(default_factory=list)
    processed_artifacts: List[DatasetArtifactEntry] = field(default_factory=list)
    split_counts: Dict[str, int] = field(default_factory=dict)
    label_distribution: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def save(self, target_dir: Union[str, Path]) -> Path:
        """Write manifest.json into the target directory."""
        p = Path(target_dir) / "manifest.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
        return p

    @classmethod
    def load(cls, target_dir_or_file: Union[str, Path]) -> DatasetManifest:
        """Load a DatasetManifest from a directory or json file."""
        p = Path(target_dir_or_file)
        if p.is_dir():
            p = p / "manifest.json"
        if not p.exists():
            raise FileNotFoundError(f"Manifest file not found at {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_artifacts = [
            DatasetArtifactEntry(**a) if isinstance(a, dict) else a
            for a in data.get("raw_artifacts", [])
        ]
        proc_artifacts = [
            DatasetArtifactEntry(**a) if isinstance(a, dict) else a
            for a in data.get("processed_artifacts", [])
        ]
        return cls(
            dataset_name=data["dataset_name"],
            version=data["version"],
            license=data["license"],
            source_uri=data["source_uri"],
            status=data["status"],
            download_timestamp=data["download_timestamp"],
            raw_artifacts=raw_artifacts,
            processed_artifacts=proc_artifacts,
            split_counts=data.get("split_counts", {}),
            label_distribution=data.get("label_distribution", {}),
            metadata=data.get("metadata", {}),
        )


class DatasetDownloader:
    """Downloader and ingestion manager for TrustRAG research benchmark datasets."""

    def __init__(
        self,
        *,
        raw_root: Union[str, Path] = "data/raw",
        processed_root: Union[str, Path] = "data/processed",
        offline: bool = False,
    ) -> None:
        self.raw_root = Path(raw_root)
        self.processed_root = Path(processed_root)
        self.offline = offline

    def download_url(
        self,
        url: str,
        dest_path: Union[str, Path],
        *,
        expected_sha256: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        chunk_size: int = 65536,
    ) -> Path:
        """Download a file with resume support, retries, and atomic writing."""
        if self.offline:
            raise AcquisitionError(f"Cannot download '{url}' in offline mode.")

        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists() and expected_sha256:
            if compute_file_sha256(dest).lower() == expected_sha256.lower():
                logger.info("File '%s' already exists and matches expected SHA-256.", dest.name)
                return dest

        tmp_dest = dest.with_suffix(dest.suffix + ".part")

        headers = {"User-Agent": "TrustRAG-Downloader/1.0 (Mozilla/5.0)"}
        existing_size = tmp_dest.stat().st_size if tmp_dest.exists() else 0

        for attempt in range(1, max_retries + 1):
            try:
                req_headers = dict(headers)
                if existing_size > 0:
                    req_headers["Range"] = f"bytes={existing_size}-"

                req = urllib.request.Request(url, headers=req_headers)
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    # Check for partial content response
                    status_code = getattr(response, "status", 200)
                    mode = "ab" if (existing_size > 0 and status_code == 206) else "wb"
                    if mode == "wb":
                        existing_size = 0

                    with open(tmp_dest, mode) as f:
                        while chunk := response.read(chunk_size):
                            f.write(chunk)

                # Move tmp to target atomically
                tmp_dest.replace(dest)
                break
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                logger.warning("Download attempt %d/%d failed for %s: %s", attempt, max_retries, url, e)
                if attempt == max_retries:
                    raise AcquisitionError(f"Failed to download '{url}' after {max_retries} attempts: {e}")
                time.sleep(2**attempt)

        actual_sha = compute_file_sha256(dest)
        if expected_sha256 and actual_sha.lower() != expected_sha256.lower():
            dest.unlink(missing_ok=True)
            raise ValidationError(
                f"SHA-256 checksum mismatch for '{dest.name}': expected {expected_sha256}, got {actual_sha}"
            )

        return dest

    def acquire_ragtruth(self, *, force: bool = False) -> DatasetManifest:
        """Acquire canonical RAGTruth from ParticleMedia/RAGTruth and prepare splits."""
        dataset_name = "ragtruth"
        info = CANONICAL_SOURCES[dataset_name]
        raw_dir = self.raw_root / dataset_name
        proc_dir = self.processed_root / dataset_name
        raw_dir.mkdir(parents=True, exist_ok=True)
        proc_dir.mkdir(parents=True, exist_ok=True)

        resp_file = raw_dir / "response.jsonl"
        src_file = raw_dir / "source_info.jsonl"

        # Download raw files if needed
        if not resp_file.exists() or force:
            logger.info("Downloading RAGTruth response.jsonl...")
            self.download_url(info["response_url"], resp_file)
        if not src_file.exists() or force:
            logger.info("Downloading RAGTruth source_info.jsonl...")
            self.download_url(info["source_info_url"], src_file)

        resp_sha = compute_file_sha256(resp_file)
        src_sha = compute_file_sha256(src_file)
        resp_size = resp_file.stat().st_size
        src_size = src_file.stat().st_size

        # Ingest and index sources
        sources: Dict[int, Dict[str, Any]] = {}
        with open(src_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    sources[int(item["source_id"])] = item

        # Join responses with source contexts and organize into native splits
        splits_data: Dict[str, List[Dict[str, Any]]] = {"train": [], "validation": [], "test": []}
        label_dist: Dict[str, int] = {"FACTUAL": 0, "HALLUCINATED": 0}

        with open(resp_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                resp_item = json.loads(line)
                sid = int(resp_item["source_id"])
                src_item = sources.get(sid, {})

                # Native split mapping
                native_split = str(resp_item.get("split", "train")).lower()
                split_key = "validation" if native_split in ("val", "validation") else ("test" if native_split == "test" else "train")

                # Label determination
                labels_list = resp_item.get("labels", [])
                label = "HALLUCINATED" if (isinstance(labels_list, list) and len(labels_list) > 0) else "FACTUAL"
                label_dist[label] += 1

                record = {
                    "record_id": f"ragtruth_{resp_item['id']}",
                    "source_id": str(sid),
                    "document": src_item.get("source_info", ""),
                    "claim": resp_item.get("response", ""),
                    "label": label,
                    "source_dataset": dataset_name,
                    "source_split": split_key,
                    "metadata": {
                        "task_type": src_item.get("task_type"),
                        "source": src_item.get("source"),
                        "prompt": src_item.get("prompt"),
                        "model": resp_item.get("model"),
                        "temperature": resp_item.get("temperature"),
                        "hallucination_spans": labels_list,
                    },
                }
                splits_data[split_key].append(record)

        # Write processed splits
        proc_artifacts: List[DatasetArtifactEntry] = []
        split_counts: Dict[str, int] = {}

        for sp_name, records in splits_data.items():
            sp_path = proc_dir / f"{sp_name}.jsonl"
            with open(sp_path, "w", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            sha = compute_file_sha256(sp_path)
            cnt = len(records)
            split_counts[sp_name] = cnt
            proc_artifacts.append(
                DatasetArtifactEntry(
                    file_name=sp_path.name,
                    relative_path=str(sp_path.relative_to(self.processed_root.parent)),
                    file_size_bytes=sp_path.stat().st_size,
                    sha256=sha,
                    record_count=cnt,
                )
            )

        raw_artifacts = [
            DatasetArtifactEntry(
                file_name=resp_file.name,
                relative_path=str(resp_file.relative_to(self.raw_root.parent)),
                file_size_bytes=resp_size,
                sha256=resp_sha,
                record_count=sum(split_counts.values()),
            ),
            DatasetArtifactEntry(
                file_name=src_file.name,
                relative_path=str(src_file.relative_to(self.raw_root.parent)),
                file_size_bytes=src_size,
                sha256=src_sha,
                record_count=len(sources),
            ),
        ]

        manifest = DatasetManifest(
            dataset_name=dataset_name,
            version=info["version"],
            license=info["license"],
            source_uri=info["repo"],
            status="READY_FOR_EXPERIMENTS",
            download_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_artifacts=raw_artifacts,
            processed_artifacts=proc_artifacts,
            split_counts=split_counts,
            label_distribution=label_dist,
            metadata={"canonical_records": info["expected_records"], "total_sources": len(sources)},
        )
        manifest.save(proc_dir)
        manifest.save(raw_dir)
        return manifest

    def acquire_halueval(self, *, force: bool = False, seed: int = 42) -> DatasetManifest:
        """Acquire canonical HaluEval QA from RUCAIBox/HaluEval and generate splits."""
        dataset_name = "halueval"
        info = CANONICAL_SOURCES[dataset_name]
        raw_dir = self.raw_root / dataset_name
        proc_dir = self.processed_root / dataset_name
        raw_dir.mkdir(parents=True, exist_ok=True)
        proc_dir.mkdir(parents=True, exist_ok=True)

        qa_file = raw_dir / "qa_data.json"
        if not qa_file.exists() or force:
            logger.info("Downloading HaluEval qa_data.json...")
            self.download_url(info["qa_url"], qa_file)

        qa_sha = compute_file_sha256(qa_file)
        qa_size = qa_file.stat().st_size

        # Ingest QA items
        items: List[Dict[str, Any]] = []
        with open(qa_file, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if line.strip():
                    item = json.loads(line)
                    item["_original_index"] = idx
                    items.append(item)

        # Deterministic 70/15/15 train/val/test split
        rng = random.Random(seed)
        shuffled = list(items)
        rng.shuffle(shuffled)

        n = len(shuffled)
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)

        split_items = {
            "train": shuffled[:n_train],
            "validation": shuffled[n_train : n_train + n_val],
            "test": shuffled[n_train + n_val :],
        }

        # Convert to ClaimVerificationRecords (pair of factual and hallucinated)
        splits_data: Dict[str, List[Dict[str, Any]]] = {"train": [], "validation": [], "test": []}
        label_dist: Dict[str, int] = {"FACTUAL": 0, "HALLUCINATED": 0}

        for sp_name, raw_list in split_items.items():
            for raw_item in raw_list:
                item_idx = raw_item["_original_index"]
                doc = str(raw_item.get("knowledge", ""))
                q = str(raw_item.get("question", ""))
                right_ans = str(raw_item.get("right_answer", ""))
                hallu_ans = str(raw_item.get("hallucinated_answer", ""))

                # Factual record
                splits_data[sp_name].append({
                    "record_id": f"halueval_{item_idx}_factual",
                    "source_id": str(item_idx),
                    "document": doc,
                    "claim": right_ans,
                    "label": "FACTUAL",
                    "source_dataset": dataset_name,
                    "source_split": sp_name,
                    "metadata": {"query": q, "pair_type": "right_answer"},
                })
                label_dist["FACTUAL"] += 1

                # Hallucinated record
                splits_data[sp_name].append({
                    "record_id": f"halueval_{item_idx}_hallucinated",
                    "source_id": str(item_idx),
                    "document": doc,
                    "claim": hallu_ans,
                    "label": "HALLUCINATED",
                    "source_dataset": dataset_name,
                    "source_split": sp_name,
                    "metadata": {"query": q, "pair_type": "hallucinated_answer"},
                })
                label_dist["HALLUCINATED"] += 1

        # Write processed splits
        proc_artifacts: List[DatasetArtifactEntry] = []
        split_counts: Dict[str, int] = {}

        for sp_name, records in splits_data.items():
            sp_path = proc_dir / f"{sp_name}.jsonl"
            with open(sp_path, "w", encoding="utf-8") as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")

            sha = compute_file_sha256(sp_path)
            cnt = len(records)
            split_counts[sp_name] = cnt
            proc_artifacts.append(
                DatasetArtifactEntry(
                    file_name=sp_path.name,
                    relative_path=str(sp_path.relative_to(self.processed_root.parent)),
                    file_size_bytes=sp_path.stat().st_size,
                    sha256=sha,
                    record_count=cnt,
                )
            )

        raw_artifacts = [
            DatasetArtifactEntry(
                file_name=qa_file.name,
                relative_path=str(qa_file.relative_to(self.raw_root.parent)),
                file_size_bytes=qa_size,
                sha256=qa_sha,
                record_count=len(items),
            )
        ]

        manifest = DatasetManifest(
            dataset_name=dataset_name,
            version=info["version"],
            license=info["license"],
            source_uri=info["repo"],
            status="READY_FOR_EXPERIMENTS",
            download_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_artifacts=raw_artifacts,
            processed_artifacts=proc_artifacts,
            split_counts=split_counts,
            label_distribution=label_dist,
            metadata={
                "canonical_qa_pairs": len(items),
                "total_claims": sum(split_counts.values()),
                "split_seed": seed,
            },
        )
        manifest.save(proc_dir)
        manifest.save(raw_dir)
        return manifest

    def acquire_hotpotqa_validation(self, *, force: bool = False) -> DatasetManifest:
        """Acquire canonical HotpotQA distractor validation split (7,405 records)."""
        dataset_name = "hotpotqa"
        info = CANONICAL_SOURCES[dataset_name]
        raw_dir = self.raw_root / dataset_name
        proc_dir = self.processed_root / dataset_name
        raw_dir.mkdir(parents=True, exist_ok=True)
        proc_dir.mkdir(parents=True, exist_ok=True)

        parquet_file = raw_dir / "hotpotqa_val_distractor.parquet"
        if not parquet_file.exists() or force:
            logger.info("Downloading HotpotQA validation parquet...")
            self.download_url(info["parquet_url"], parquet_file)

        sha_raw = compute_file_sha256(parquet_file)
        raw_size = parquet_file.stat().st_size

        # Ingest parquet into JSONL
        try:
            import pandas as pd  # type: ignore
        except ImportError:
            raise AcquisitionError("pandas is required to read parquet files.")

        df = pd.read_parquet(parquet_file)
        records: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            qid = str(row.get("id", ""))
            q = str(row.get("question", ""))
            ans = str(row.get("answer", ""))

            # Supporting facts
            supp_facts = row.get("supporting_facts")
            rel_docs = []
            if isinstance(supp_facts, dict) and "title" in supp_facts:
                rel_docs = [str(t) for t in supp_facts["title"]]
            elif isinstance(supp_facts, list):
                rel_docs = [str(f[0]) for f in supp_facts if len(f) > 0]

            records.append({
                "query_id": qid,
                "query": q,
                "answer": ans,
                "source_dataset": dataset_name,
                "source_split": "validation",
                "source_id": qid,
                "relevant_document_ids": rel_docs,
                "metadata": {
                    "level": row.get("level"),
                    "type": row.get("type"),
                },
            })

        val_jsonl = proc_dir / "validation.jsonl"
        with open(val_jsonl, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        val_sha = compute_file_sha256(val_jsonl)
        cnt = len(records)

        manifest = DatasetManifest(
            dataset_name=dataset_name,
            version=info["version"],
            license=info["license"],
            source_uri=f"https://huggingface.co/datasets/{info['hf_repo']}",
            status="READY_FOR_EXPERIMENTS",
            download_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_artifacts=[
                DatasetArtifactEntry(
                    file_name=parquet_file.name,
                    relative_path=str(parquet_file.relative_to(self.raw_root.parent)),
                    file_size_bytes=raw_size,
                    sha256=sha_raw,
                    record_count=cnt,
                )
            ],
            processed_artifacts=[
                DatasetArtifactEntry(
                    file_name=val_jsonl.name,
                    relative_path=str(val_jsonl.relative_to(self.processed_root.parent)),
                    file_size_bytes=val_jsonl.stat().st_size,
                    sha256=val_sha,
                    record_count=cnt,
                )
            ],
            split_counts={"validation": cnt},
            label_distribution={},
            metadata={"config": info["config"], "expected_records": info["expected_records"]},
        )
        manifest.save(proc_dir)
        manifest.save(raw_dir)
        return manifest

    def acquire_ms_marco_validation(self, *, force: bool = False) -> DatasetManifest:
        """Acquire canonical MS MARCO v1.1 validation split (10,047 records)."""
        dataset_name = "ms_marco"
        info = CANONICAL_SOURCES[dataset_name]
        raw_dir = self.raw_root / dataset_name
        proc_dir = self.processed_root / dataset_name
        raw_dir.mkdir(parents=True, exist_ok=True)
        proc_dir.mkdir(parents=True, exist_ok=True)

        parquet_file = raw_dir / "ms_marco_val_v1.1.parquet"
        if not parquet_file.exists() or force:
            logger.info("Downloading MS MARCO validation parquet...")
            self.download_url(info["parquet_url"], parquet_file)

        sha_raw = compute_file_sha256(parquet_file)
        raw_size = parquet_file.stat().st_size

        try:
            import pandas as pd  # type: ignore
        except ImportError:
            raise AcquisitionError("pandas is required to read parquet files.")

        df = pd.read_parquet(parquet_file)
        records: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            qid = str(row.get("query_id", ""))
            q = str(row.get("query", ""))
            answers = row.get("answers", [])
            ans_str = answers[0] if isinstance(answers, (list, tuple)) and len(answers) > 0 else ""

            passages = row.get("passages", {})
            passages_text = passages.get("passage_text", []) if isinstance(passages, dict) else []

            records.append({
                "query_id": qid,
                "query": q,
                "answer": ans_str,
                "source_dataset": dataset_name,
                "source_split": "validation",
                "source_id": qid,
                "relevant_document_ids": [],
                "metadata": {
                    "query_type": row.get("query_type"),
                    "passage_count": len(passages_text),
                },
            })

        val_jsonl = proc_dir / "validation.jsonl"
        with open(val_jsonl, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        val_sha = compute_file_sha256(val_jsonl)
        cnt = len(records)

        manifest = DatasetManifest(
            dataset_name=dataset_name,
            version=info["version"],
            license=info["license"],
            source_uri=f"https://huggingface.co/datasets/{info['hf_repo']}",
            status="READY_FOR_EXPERIMENTS",
            download_timestamp=datetime.now(timezone.utc).isoformat(),
            raw_artifacts=[
                DatasetArtifactEntry(
                    file_name=parquet_file.name,
                    relative_path=str(parquet_file.relative_to(self.raw_root.parent)),
                    file_size_bytes=raw_size,
                    sha256=sha_raw,
                    record_count=cnt,
                )
            ],
            processed_artifacts=[
                DatasetArtifactEntry(
                    file_name=val_jsonl.name,
                    relative_path=str(val_jsonl.relative_to(self.processed_root.parent)),
                    file_size_bytes=val_jsonl.stat().st_size,
                    sha256=val_sha,
                    record_count=cnt,
                )
            ],
            split_counts={"validation": cnt},
            label_distribution={},
            metadata={"config": info["config"], "expected_records": info["expected_records"]},
        )
        manifest.save(proc_dir)
        manifest.save(raw_dir)
        return manifest

    def probe_dataset_access(self, dataset_name: str) -> Dict[str, Any]:
        """Probe access, gating, and license status for a dataset."""
        if dataset_name not in CANONICAL_SOURCES:
            return {"status": "UNKNOWN_DATASET", "error": f"Dataset {dataset_name} not registered."}

        info = CANONICAL_SOURCES[dataset_name]

        if dataset_name == "llm_aggrefact":
            # Gated repository check
            hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
            req = urllib.request.Request(
                f"https://huggingface.co/api/datasets/{info['hf_repo']}",
                headers={"User-Agent": "TrustRAG-Probe/1.0"},
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    data = json.loads(r.read().decode())
                    is_gated = data.get("gated", False)
                    if is_gated and not hf_token:
                        return {
                            "dataset_name": dataset_name,
                            "status": "ACCESS_BLOCKED",
                            "reason": "Repository is gated on Hugging Face Hub. User must accept license agreement and provide HF_TOKEN.",
                            "license": info["license"],
                            "url": info["url"],
                        }
                    return {"dataset_name": dataset_name, "status": "AVAILABLE", "license": info["license"]}
            except urllib.error.HTTPError as e:
                return {
                    "dataset_name": dataset_name,
                    "status": "ACCESS_BLOCKED",
                    "reason": f"HTTP {e.code}: {e.reason}",
                    "license": info["license"],
                    "url": info["url"],
                }

        if dataset_name == "rsb":
            return {
                "dataset_name": dataset_name,
                "status": "ACCESS_BLOCKED",
                "reason": "No public direct download URL or canonical Hugging Face repository exists. Academic paper arXiv:2505.18543 requires local research artifact import.",
                "license": info["license"],
                "paper": info["paper"],
            }

        return {"dataset_name": dataset_name, "status": "AVAILABLE", "license": info.get("license")}


__all__ = [
    "DatasetDownloader",
    "DatasetManifest",
    "DatasetArtifactEntry",
    "CANONICAL_SOURCES",
    "compute_file_sha256",
]
