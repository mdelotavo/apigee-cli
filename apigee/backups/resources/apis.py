import os
import asyncio
from requests.exceptions import HTTPError

from apigee import console
from apigee.apis.apis import Apis
from apigee.utils import extract_zip_file
from ..base import BaseBackup
from ..utils import run_blocking


class APIsBackup(BaseBackup):

    async def snapshot(self):
        client = Apis(self.config.authentication, self.config.org_name)

        apis = await run_blocking(
          client.list_api_proxies,
          self.config.prefix,
          "dict",
        )

        result = {}

        async def fetch(api):
            try:
                resp = await run_blocking(client.get_api_proxy, api)
                return api, resp.json()
            except Exception as e:
                self.handle_error(e, api)
                return api, {}

        tasks = [asyncio.create_task(fetch(api)) for api in apis]
        results = await asyncio.gather(*tasks)

        for api, data in results:
            result[api] = data

        return result

    def save_snapshot(self, data):
        self.config.snapshot_data.apis = data

        for api, content in data.items():
            path = self.full_path(f"snapshots/apis/{api}.json")
            from apigee.utils import write_content_to_file
            write_content_to_file(content, path, indentation=2)

    async def download(self):
        tasks = []
        total = 0

        for api, meta in self.config.snapshot_data.apis.items():
            count = len(meta.get("revision", []))
            total += count
            console.echo(f"  {api}: {count} revisions")

        console.echo(f"  Total API revisions to download: {total}")

        self.config.total_items = getattr(self.config, "total_items", 0) + total

        client = Apis(self.config.authentication, self.config.org_name)

        for api, meta in self.config.snapshot_data.apis.items():
            for revision in meta.get("revision", []):
                tasks.append(asyncio.create_task(self._download(client, api, revision)))

        await asyncio.gather(*tasks)

    async def _download(self, client, api, revision):
        try:
            output = self.full_path(f"apis/{api}/{revision}/{api}.zip")
            work_dir = os.path.dirname(output)

            await run_blocking(
              client.export_api_proxy,
              api,
              revision,
              True,
              str(output),
            )

            await run_blocking(extract_zip_file, str(output), work_dir)
            await run_blocking(os.remove, str(output))

            self.progress("APIs")

        except HTTPError as e:
            if e.response.status_code == 404:
                self.handle_http_error(e, f" for API ({api}, rev {revision})")
                return
            raise

        except Exception as e:
            self.handle_error(e, api, revision)
