import asyncio
from requests.exceptions import HTTPError

from apigee.apps.apps import Apps
from apigee.developers.developers import Developers
from apigee.utils import write_content_to_file, filter_out_empty_values

from ..base import BaseBackup
from ..utils import run_blocking


class AppsBackup(BaseBackup):

    async def snapshot(self):
        # Step 1: get all developers
        developers = await run_blocking(
          Developers(self.config.authentication, self.config.org_name, None).list_developers,
          None,  # prefix handled later
          False,  # expand
          1000,
          "",
          "dict",
        )

        # Step 2: get apps for all developers
        apps = await run_blocking(
          Apps(self.config.authentication, self.config.org_name, None).list_apps_for_all_developers,
          developers,
          self.config.prefix,
          "dict",
        )

        # Step 3: remove empty values (same as original logic)
        apps = filter_out_empty_values(apps)

        return apps

    def save_snapshot(self, data):
        self.config.snapshot_data.apps = data

        # NOTE: data structure is:
        # { developer: [app1, app2, ...] }

        for developer, apps in data.items():
            for app in apps:
                path = self.full_path(f"snapshots/apps/{app}.json")

                # snapshot stores just the name (consistent with original)
                write_content_to_file(app, path, indentation=2)

    async def download(self):
        tasks = []

        for developer, apps in self.config.snapshot_data.apps.items():
            for app in apps:
                tasks.append(self._download(developer, app))

        await asyncio.gather(*tasks)

    async def _download(self, developer, app):
        try:
            content = await run_blocking(
              Apps(self.config.authentication, self.config.org_name, app).get_developer_app_details,
              developer,
            )

            path = self.full_path(f"apps/{developer}/{app}.json")

            await run_blocking(
              write_content_to_file,
              content.text,
              path,
              2,
            )

            self.progress("Apps")

        except HTTPError as e:
            self.handle_http_error(e, f" for Developer App ({app})")
        except Exception as e:
            self.handle_error(e, developer, app)
