import asyncio

from requests.exceptions import HTTPError

from apigee import console
from apigee.developers.developers import Developers
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class DevelopersBackup(BaseBackup):

    async def snapshot(self):
        client = Developers(self.config.authentication, self.config.org_name, None)

        return await run_blocking(
          client.list,
          self.config.prefix,
          False,
          1000,
          "",
          "dict",
        )

    def save_snapshot(self, data):
        self.config.snapshot_data.developers = data

        path = self.full_path("snapshots/developers/developers.json")
        write_content_to_file(data, path, indentation=2)

    async def download(self):
        tasks = []
        total = len(self.config.snapshot_data.developers)

        console.echo(f"  Total developers to download: {total}")

        self.config.total_items = getattr(self.config, "total_items", 0) + total

        for developer in self.config.snapshot_data.developers:
            tasks.append(asyncio.create_task(self._download(developer)))

        await asyncio.gather(*tasks)

    async def _download(self, developer):
        try:
            client = Developers(self.config.authentication, self.config.org_name, developer)

            resp = await run_blocking(client.get, )

            path = self.full_path(f"developers/{developer}.json")

            await run_blocking(write_content_to_file, resp.text, path, 2)

            self.progress("Developers")

        except HTTPError as e:
            if e.response.status_code == 404:
                self.handle_http_error(e, f" for developer ({developer})")
                return
            raise

        except Exception as e:
            self.handle_error(e, developer)
