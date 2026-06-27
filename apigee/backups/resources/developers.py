import asyncio

from requests.exceptions import HTTPError
from apigee.developers.developers import Developers
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class DevelopersBackup(BaseBackup):

    async def snapshot(self):
        return await run_blocking(Developers(self.config.authentication, self.config.org_name, None).list_developers, self.config.prefix, "dict")

    def save_snapshot(self, data):
        self.config.snapshot_data.developers = data

        path = self.full_path("snapshots/developers/developers.json")
        write_content_to_file(data, path, indentation=2)

    async def download(self):
        tasks = [self._download(dev) for dev in self.config.snapshot_data.developers]
        await asyncio.gather(*tasks)

    async def _download(self, developer):
        try:
            content = await run_blocking(Developers(self.config.authentication, self.config.org_name, developer).get_developer)

            path = self.full_path(f"developers/{developer}.json")

            await run_blocking(write_content_to_file, content.text, path, 2)

            self.progress("Developers")

        except HTTPError as e:
            self.handle_http_error(e, f" for developer ({developer})")
        except Exception as e:
            self.handle_error(e, developer)
