import asyncio
from requests.exceptions import HTTPError

from apigee import console
from apigee.caches.caches import Caches
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class CachesBackup(BaseBackup):

    async def snapshot(self):
        result = {}

        client = Caches(self.config.authentication, self.config.org_name, None)

        for env in self.config.environments:
            caches = await run_blocking(
              client.list,
              env,
              self.config.prefix,
              "dict",
            )
            result[env] = caches

        return result

    def save_snapshot(self, data):
        self.config.snapshot_data.caches = data

        for env, caches in data.items():
            path = self.full_path(f"snapshots/caches/{env}/caches.json")
            write_content_to_file(caches, path, indentation=2)

    async def download(self):
        tasks = []
        total = 0

        for env, caches in self.config.snapshot_data.caches.items():
            count = len(caches)
            total += count
            console.echo(f"  {env}: {count} caches")

        console.echo(f"  Total caches to download: {total}")

        self.config.total_items = getattr(self.config, "total_items", 0) + total

        for env, caches in self.config.snapshot_data.caches.items():
            for cache in caches:
                tasks.append(asyncio.create_task(self._download(env, cache)))

        await asyncio.gather(*tasks)

    async def _download(self, env, cache):
        try:
            client = Caches(self.config.authentication, self.config.org_name, cache)

            resp = await run_blocking(
              client.get,
              env,
            )

            path = self.full_path(f"caches/{env}/{cache}.json")

            await run_blocking(write_content_to_file, resp.text, path, 2)

            self.progress("Caches")

        except HTTPError as e:
            if e.response.status_code == 404:
                self.handle_http_error(e, f" for Cache ({cache})")
                return
            raise

        except Exception as e:
            self.handle_error(e, env, cache)
