# conflux/core/registry.py
from typing import Dict, Tuple

TranslatorKey = Tuple[str, str]  # (src, dst)

_registry: Dict[TranslatorKey, object] = {}

def register(translator: object):
    key = (getattr(translator, "src"), getattr(translator, "dst"))
    _registry[key] = translator

def get(src: str, dst: str) -> object:
    try:
        return _registry[(src, dst)]
    except KeyError:
        raise ValueError(f"No translator registered for {src}→{dst}")

def list_pairs():
    return sorted(_registry.keys())