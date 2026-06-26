from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Optional
from tqdm import tqdm

from apigee.types import Struct, empty_snapshot
from apigee.utils import get_resolved_directory_path


@dataclass
class BackupConfig:
    api_choices: Set[str]
    authentication: Struct
    environments: List[str]
    org_name: str
    prefix: Optional[str]
    working_directory: str

    snapshot_data: Struct = empty_snapshot()
    progress_bar: Optional[tqdm] = None
    working_org_directory: Optional[Path] = None

    def __post_init__(self):
        self.api_choices = set(self.api_choices or [])
        self.environments = self.environments or []

        self.working_directory = get_resolved_directory_path(self.working_directory)
        self.working_org_directory = Path(self.working_directory) / self.org_name
