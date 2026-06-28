import asyncio
from requests.exceptions import HTTPError

from apigee import console
from apigee.targetservers.targetservers import Targetservers
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class TargetServersBackup(BaseBackup):

    async def snapshot(self):
        result = {}

        client = Targetservers(self.config.authentication, self.config.org_name, None)

        for env in self.config.environments:
            targets = await run_blocking(
              client.list,
              env,
              self.config.prefix,
              "dict",
            )
            result[env] = targets

        return result

    def save_snapshot(self, data):
        self.config.snapshot_data.targetservers = data

        for env, targets in data.items():
            path = self.full_path(f"snapshots/targetservers/{env}/targetservers.json")
            write_content_to_file(targets, path, indentation=2)

    async def download(self):
        tasks = []
        total = 0

        for env, targets in self.config.snapshot_data.targetservers.items():
            count = len(targets)
            total += count
            console.echo(f"  {env}: {count} targetservers")

        console.echo(f"  Total targetservers to download: {total}")

        self.config.total_items = getattr(self.config, "total_items", 0) + total

        for env, targets in self.config.snapshot_data.targetservers.items():
            for target in targets:
                tasks.append(asyncio.create_task(self._download(env, target)))

        await asyncio.gather(*tasks)

    async def _download(self, env, target):
        try:
            client = Targetservers(self.config.authentication, self.config.org_name, target)

            resp = await run_blocking(
              client.get,
              env,
            )

            path = self.full_path(f"targetservers/{env}/{target}.json")

            await run_blocking(write_content_to_file, resp.text, path, 2)

            self.progress("TargetServers")

        except HTTPError as e:
            if e.response.status_code == 404:
                self.handle_http_error(e, f" for TargetServer ({target})")
                return
            raise

        except Exception as e:
            self.handle_error(e, env, target)
