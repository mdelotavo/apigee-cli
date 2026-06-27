import os
import asyncio

from apigee.apis.apis import Apis
from apigee.utils import extract_zip_file, write_content_to_file
from requests.exceptions import HTTPError

from ..base import BaseBackup
from ..utils import run_blocking


class APIsBackup(BaseBackup):

    async def snapshot(self):
        apis = await run_blocking(Apis(self.config.authentication, self.config.org_name).list_api_proxies, self.config.prefix, "dict")

        async def fetch(api):
            try:
                data = await run_blocking(Apis(self.config.authentication, self.config.org_name).get_api_proxy(api).json)
                return api, data
            except Exception as e:
                self.handle_error(e, api)
                return api, {}

        results = await asyncio.gather(*[fetch(api) for api in apis])
        return dict(results)

    def save_snapshot(self, data):
        self.config.snapshot_data.apis = data

        for api, content in data.items():
            path = self.full_path(f"snapshots/apis/{api}.json")
            write_content_to_file(content, path, indentation=2)

    async def download(self):
        tasks = []

        for api, meta in self.config.snapshot_data.apis.items():
            for rev in meta.get("revision", []):
                tasks.append(self._download(api, rev))

        await asyncio.gather(*tasks)

    async def _download(self, api, revision):
        try:
            output = self.full_path(f"apis/{api}/{revision}/{api}.zip")
            work_dir = os.path.dirname(output)

            await run_blocking(
              Apis(self.config.authentication, self.config.org_name).export_api_proxy,
              api,
              revision,
              True,
              str(output),
            )

            await run_blocking(extract_zip_file, str(output), work_dir)
            await run_blocking(os.remove, str(output))

            self.progress("APIs")

        except HTTPError as e:
            self.handle_http_error(e, f" for API ({api}, rev {revision})")
        except Exception as e:
            self.handle_error(e, api, revision)
