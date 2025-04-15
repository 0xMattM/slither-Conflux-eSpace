from pathlib import Path
from typing import Optional

def get_conflux_dir() -> Path:
    """Return the path to the conflux_espace directory"""
    return Path(__file__).parent

def get_script_path(script_name: str) -> Optional[Path]:
    """Return the path to a script in the conflux_espace directory"""
    script_path = get_conflux_dir() / script_name
    return script_path if script_path.exists() else None

__all__ = [
    'get_conflux_dir',
    'get_script_path'
]
