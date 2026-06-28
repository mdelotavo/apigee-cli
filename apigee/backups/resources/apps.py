import asyncio
from requests.exceptions import HTTPError

from apigee import console
from apigee.apps.apps import Apps
from apigee.developers.developers import Developers
from apigee.utils import write_content_to_file, filter_out_empty_values

from ..base import BaseBackup
from ..utils import run_blocking


class AppsBackup(BaseBackup):

    async def snapshot(self):
        dev_client = Developers(self.config.authentication, self.config.org_name, None)

        developers = await run_blocking(
          dev_client.list,
          None,
          False,
          1000,
          "",
          "dict",
        )

        apps_client = Apps(self.config.authentication, self.config.org_name, None)

        apps = {}

        async def fetch(dev):
            try:
                result = await run_blocking(
                  apps_client.list,
                  dev,
                  self.config.prefix,
                  False,
                  1000,
                  "",
                  "dict",
                )
                return dev, result
            except Exception as e:
                self.handle_error(e, dev)
                return dev, []

        tasks = [asyncio.create_task(fetch(dev)) for dev in developers]
        results = await asyncio.gather(*tasks)

        for dev, dev_apps in results:
            apps[dev] = dev_apps

        apps = filter_out_empty_values(apps)

        return apps

    def save_snapshot(self, data):
        self.config.snapshot_data.apps = data

        for developer, apps in data.items():
            path = self.full_path(f"snapshots/apps/{developer}.json")
            write_content_to_file(apps, path, indentation=2)

    async def download(self):
        tasks = []
        total = 0

        for developer, apps in self.config.snapshot_data.apps.items():
            count = len(apps)
            total += count
            console.echo(f"  {developer}: {count} apps")

        console.echo(f"  Total apps to download: {total}")

        self.config.total_items = getattr(self.config, "total_items", 0) + total

        for developer, apps in self.config.snapshot_data.apps.items():
            for app in apps:
                tasks.append(asyncio.create_task(self._download(developer, app)))

        await asyncio.gather(*tasks)

    async def _download(self, developer, app):
        try:
            client = Apps(self.config.authentication, self.config.org_name, app)

            resp = await run_blocking(
              client.get,
              developer,
            )

            path = self.full_path(f"apps/{developer}/{app}.json")

            await run_blocking(
              write_content_to_file,
              resp.text,
              path,
              2,
            )

            self.progress("Apps")

        except HTTPError as e:
            if e.response.status_code == 404:
                self.handle_http_error(e, f" for Developer App ({app})")
                return
            raise

        except Exception as e:
            self.handle_error(e, developer, app)
