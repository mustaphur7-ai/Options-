"""Load config.yaml."""
from pathlib import Path
from typing import Any, Dict

import yaml


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    with open(Path(path), "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
