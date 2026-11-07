# src/trustrag/utils/repro.py
"""Reproducibility helpers for TrustRAG.

* ``set_random_seed`` – sets seeds for ``random``, ``numpy`` and, if available,
  ``torch`` (including CUDA). It logs the actions using the project logger.
* ``get_hardware_info`` – returns a dictionary with basic hardware information:
  CPU count, total memory (via ``psutil`` if installed), and whether a CUDA‑
  capable GPU is detected (via ``torch.cuda`` when ``torch`` is available).
"""

from __future__ import annotations

import random
import os
import logging
from typing import Any, Dict

import numpy as np

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover – optional dependency
    torch = None  # type: ignore

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover – optional dependency
    psutil = None  # type: ignore

from .logging import get_logger

LOGGER = get_logger(__name__)


def set_random_seed(seed: int) -> None:
    """Set random seeds for reproducibility.

    Parameters
    ----------
    seed: int
        The seed value to use.
    """
    random.seed(seed)
    np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    LOGGER.info("Random seed set", extra={"seed": seed})


def get_hardware_info() -> Dict[str, Any]:
    """Return a dictionary describing the host hardware.

    The function is tolerant of missing optional packages and will omit fields
    that cannot be determined.
    """
    info: Dict[str, Any] = {
        "cpu_count": os.cpu_count(),
    }
    if psutil is not None:
        info["memory_total_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
    if torch is not None:
        info["torch_version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["cuda_device_count"] = torch.cuda.device_count()
            info["cuda_device_name"] = torch.cuda.get_device_name(0)
    return info

