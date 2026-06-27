import asyncio

from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Optional
from tqdm import tqdm

from apigee.types import Struct, empty_snapshot
from apigee.utils import get_resolved_directory_path

_GLOBAL_SEMAPHORE: Optional[asyncio.Semaphore] = None


def get_global_semaphore():
    return _GLOBAL_SEMAPHORE


def set_global_semaphore(semaphore: asyncio.Semaphore):
    global _GLOBAL_SEMAPHORE
    _GLOBAL_SEMAPHORE = semaphore


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

    max_concurrency: int = 10
    semaphore: Optional[asyncio.Semaphore] = None

    def __post_init__(self):
        self.api_choices = set(self.api_choices or [])
        self.environments = self.environments or []

        self.working_directory = get_resolved_directory_path(self.working_directory)
        self.working_org_directory = Path(self.working_directory) / self.org_name

        self.semaphore = asyncio.Semaphore(self.max_concurrency)

        set_global_semaphore(self.semaphore)