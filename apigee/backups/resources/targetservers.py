import asyncio
from requests.exceptions import HTTPError

from apigee.targetservers.targetservers import Targetservers
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class TargetServersBackup(BaseBackup):

    async def snapshot(self):
        result = {}

        for env in self.config.environments:
            targets = await run_blocking(
              Targetservers(self.config.authentication, self.config.org_name, None).list_targetservers_in_an_environment,
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

        for env, targets in self.config.snapshot_data.targetservers.items():
            for target in targets:
                tasks.append(self._download(env, target))

        await asyncio.gather(*tasks)

    async def _download(self, env, target):
        try:
            content = await run_blocking(
              Targetservers(self.config.authentication, self.config.org_name, target).get_targetserver,
              env,
            )

            path = self.full_path(f"targetservers/{env}/{target}.json")

            await run_blocking(write_content_to_file, content.text, path, 2)

            self.progress("TargetServers")

        except HTTPError as e:
            self.handle_http_error(e, f" for TargetServer ({target})")
        except Exception as e:
            self.handle_error(e, env, target)
