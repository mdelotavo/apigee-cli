from abc import ABC, abstractmethod
from pathlib import Path
from tqdm import tqdm
from requests.exceptions import HTTPError

from apigee import console
from apigee.exceptions import log_and_echo_http_error


class BaseBackup(ABC):

    def __init__(self, config):
        self.config = config

    async def run(self):
        try:
            data = await self.snapshot()
            self.save_snapshot(data)
            await self.download()
        except Exception as e:
            console.echo(f"[ERROR] {self.__class__.__name__}: {e}")

    @abstractmethod
    async def snapshot(self):
        pass

    @abstractmethod
    def save_snapshot(self, data):
        pass

    @abstractmethod
    async def download(self):
        pass

    def full_path(self, subpath: str) -> Path:
        return Path(self.config.working_org_directory) / subpath

    def progress(self, label: str):
        if not self.config.progress_bar:
            self.config.progress_bar = tqdm(unit="files", leave=False)

        self.config.progress_bar.set_description(label)
        self.config.progress_bar.update(1)

    def handle_http_error(self, error: HTTPError, message: str):
        log_and_echo_http_error(error, append_message=message)

    def handle_error(self, error: Exception, *ctx):
        console.echo(f"{type(error).__name__}: {ctx}")