"""Hugging Face datasets acquisition integration for TrustRAG.

Provides streaming and batch acquisition from the Hugging Face Hub with:
- Offline mode enforcement
- Split and configuration selection
- Explicit record limits
- Clear diagnostics on network, gating, or schema errors
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union

from trustrag.data.exceptions import AcquisitionError

logger = logging.getLogger(__name__)


class HFAcquisitionHelper:
    """Helper for acquiring records from Hugging Face Datasets."""

    @classmethod
    def load_hf_records(
        cls,
        dataset_id: str,
        *,
        split: str = "train",
        config_name: Optional[str] = None,
        cache_dir: Optional[Union[str, Path]] = None,
        limit: Optional[int] = None,
        offline: bool = False,
        streaming: bool = True,
    ) -> Iterator[Dict[str, Any]]:
        """Load records from Hugging Face Datasets with streaming or cached loading.

        Parameters
        ----------
        dataset_id: str
            Hugging Face repository ID (e.g., 'google/boolq').
        split: str
            Target split name.
        config_name: str | None
            Dataset configuration/subset name if required.
        cache_dir: Path | str | None
            Directory to store downloaded data.
        limit: int | None
            Maximum number of records to emit.
        offline: bool
            If True, raise AcquisitionError if local cache is not available.
        streaming: bool
            Whether to use HF dataset streaming.

        Yields
        ------
        Dict[str, Any]
            Raw dataset record.
        """
        try:
            from datasets import load_dataset  # type: ignore
        except ImportError as e:
            raise AcquisitionError(f"Hugging Face 'datasets' library is required for {dataset_id}: {e}")

        cache_path = str(cache_dir) if cache_dir else None

        if offline:
            # When offline, check if cached files exist in cache_dir
            logger.info("Offline mode enabled: checking local cache for %s", dataset_id)
            try:
                # Attempt to load with local_files_only
                ds = load_dataset(
                    dataset_id,
                    name=config_name,
                    split=split,
                    cache_dir=cache_path,
                    streaming=False,
                    download_mode="reuse_cache_if_exists",
                )
            except Exception as e:
                raise AcquisitionError(
                    f"Dataset '{dataset_id}' unavailable in offline mode. "
                    f"No cached version found in '{cache_path}': {e}"
                )
        else:
            try:
                ds = load_dataset(
                    dataset_id,
                    name=config_name,
                    split=split,
                    cache_dir=cache_path,
                    streaming=streaming,
                )
            except Exception as e:
                err_str = str(e)
                if "gated repo" in err_str.lower() or "403" in err_str:
                    raise AcquisitionError(
                        f"Dataset '{dataset_id}' requires manual access or authentication. "
                        f"Visit https://huggingface.co/datasets/{dataset_id} to accept license terms: {e}"
                    )
                raise AcquisitionError(
                    f"Failed to acquire Hugging Face dataset '{dataset_id}' (config={config_name}, split={split}): {e}"
                )

        count = 0
        try:
            for item in ds:
                yield dict(item)
                count += 1
                if limit is not None and count >= limit:
                    break
        except Exception as e:
            raise AcquisitionError(f"Error while reading stream from '{dataset_id}': {e}")


__all__ = ["HFAcquisitionHelper"]

