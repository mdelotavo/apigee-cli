import asyncio
from requests.exceptions import HTTPError

from apigee.keyvaluemaps.keyvaluemaps import Keyvaluemaps
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class KeyValueMapsBackup(BaseBackup):

    async def snapshot(self):
        result = {}

        for env in self.config.environments:
            kvms = await run_blocking(
              Keyvaluemaps(self.config.authentication, self.config.org_name, None).list_keyvaluemaps_in_an_environment,
              env,
              self.config.prefix,
              "dict",
            )
            result[env] = kvms

        return result

    def save_snapshot(self, data):
        self.config.snapshot_data.keyvaluemaps = data

        for env, kvms in data.items():
            path = self.full_path(f"snapshots/keyvaluemaps/{env}/keyvaluemaps.json")
            write_content_to_file(kvms, path, indentation=2)

    async def download(self):
        tasks = []

        for env, kvms in self.config.snapshot_data.keyvaluemaps.items():
            for kvm in kvms:
                tasks.append(self._download(env, kvm))

        await asyncio.gather(*tasks)

    async def _download(self, env, kvm):
        try:
            content = await run_blocking(
              Keyvaluemaps(self.config.authentication, self.config.org_name, kvm).get_keyvaluemap_in_an_environment,
              env,
            )

            path = self.full_path(f"keyvaluemaps/{env}/{kvm}.json")

            await run_blocking(write_content_to_file, content.text, path, 2)

            self.progress("KeyValueMaps")

        except HTTPError as e:
            self.handle_http_error(e, f" for KVM ({kvm})")
        except Exception as e:
            self.handle_error(e, env, kvm)
