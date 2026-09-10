import os
from pathlib import Path
from typing import Optional
import yaml
from . import Article

class Config:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.sources = self._load_yaml("sources.yml")
        self.leaders = self._load_yaml("leaders.yml")
        self.anthropic_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.gmail_user = "dojoatsomernova@gmail.com"  # hardcoded; overridden in workflow
        self.email_to = "jhenny.saintsurin@outlook.com"  # hardcoded; overridden in workflow

    def _load_yaml(self, filename: str) -> dict:
        path = self.project_root / filename
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path) as f:
            data = yaml.safe_load(f)
        if not data:
            raise ValueError(f"Empty config file: {path}")
        return data
