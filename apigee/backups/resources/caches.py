import asyncio
from requests.exceptions import HTTPError

from apigee.caches.caches import Caches
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class CachesBackup(BaseBackup):

    async def snapshot(self):
        result = {}

        for env in self.config.environments:
            caches = await run_blocking(
              Caches(self.config.authentication, self.config.org_name, None).list_caches_in_an_environment,
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

        for env, caches in self.config.snapshot_data.caches.items():
            for cache in caches:
                tasks.append(self._download(env, cache))

        await asyncio.gather(*tasks)

    async def _download(self, env, cache):
        try:
            content = await run_blocking(
              Caches(self.config.authentication, self.config.org_name, cache).get_information_about_a_cache,
              env,
            )

            path = self.full_path(f"caches/{env}/{cache}.json")

            await run_blocking(write_content_to_file, content.text, path, 2)

            self.progress("Caches")

        except HTTPError as e:
            self.handle_http_error(e, f" for Cache ({cache})")
        except Exception as e:
            self.handle_error(e, env, cache)
