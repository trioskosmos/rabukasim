#!/usr/bin/env python3
"""
Performance optimization utilities for all game engine tools.
Provides caching and fast-path utilities for common operations.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional

# Global caches
_DATABASE_CACHE: Dict[str, str] = {}
_DATABASE_JSON_CACHE: Dict[str, Dict] = {}

logger = logging.getLogger(__name__)

def load_database_json_cached(db_path: str) -> Tuple[Dict, str]:
    """
    Load database JSON with global caching.
    Returns: (parsed_dict, json_string)
    """
    db_path = str(Path(db_path).resolve())
    
    if db_path not in _DATABASE_CACHE:
        with open(db_path, "r", encoding="utf-8") as f:
            db_json = f.read()
        _DATABASE_CACHE[db_path] = db_json
        _DATABASE_JSON_CACHE[db_path] = json.loads(db_json)
    
    return _DATABASE_JSON_CACHE[db_path], _DATABASE_CACHE[db_path]

def disable_debug_logging():
    """Disable debug/info logging for production speed."""
    logging.getLogger().setLevel(logging.WARNING)
    for logger_name in ['torch', 'transformers', 'engine_rust']:
        logging.getLogger(logger_name).setLevel(logging.ERROR)

def enable_torch_optimizations():
    """Enable PyTorch speed optimizations."""
    try:
        import torch
        torch.set_float32_matmul_precision('medium')  # Use TF32 on NVIDIA
        torch.backends.cudnn.benchmark = True  # Enable CNN acceleration
        torch.backends.cudnn.deterministic = False  # Slightly faster
        
        if torch.cuda.is_available():
            # Set to non-blocking GPU transfers
            torch.cuda.set_device(0)
            torch.cuda.synchronize()  # Warm up
            
    except Exception as e:
        logger.debug(f"Could not enable torch optimizations: {e}")

def fast_action_categorization(legal_ids):
    """
    Fast numpy-based action categorization (used by TurnSeq).
    Pre-allocate lists for better memory performance.
    """
    import numpy as np
    ids = np.array(list(legal_ids), dtype=np.int32)
    
    return {
        'members': ids[(ids >= 1000) & (ids < 1100)].tolist(),
        'life': ids[((ids >= 600) & (ids < 700)) | ((ids >= 900) & (ids < 1000))].tolist(),
        'school': ids[(ids >= 400) & (ids < 500)].tolist(),
        'vanilla': ids[(ids >= 200) & (ids < 300)].tolist(),
        'intro': ids[(ids >= 300) & (ids < 400)].tolist(),
    }

__all__ = [
    'load_database_json_cached',
    'disable_debug_logging',
    'enable_torch_optimizations',
    'fast_action_categorization',
]
