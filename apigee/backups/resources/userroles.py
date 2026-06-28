import asyncio
import json
from requests.exceptions import HTTPError

from apigee import console
from apigee.userroles.userroles import Userroles
from apigee.permissions.permissions import Permissions
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class UserRolesBackup(BaseBackup):

    async def snapshot(self):
        client = Userroles(self.config.authentication, self.config.org_name, None)

        resp = await run_blocking(client.list)
        roles = resp.json()

        if self.config.prefix:
            roles = [r for r in roles if r.startswith(self.config.prefix)]

        return roles

    def save_snapshot(self, data):
        self.config.snapshot_data.userroles = data

        path = self.full_path("snapshots/userroles/userroles.json")
        write_content_to_file(data, path, indentation=2)

    async def download(self):
        tasks = []
        total = len(self.config.snapshot_data.userroles)

        console.echo(f"  Total userroles to download: {total}")

        self.config.total_items = getattr(self.config, "total_items", 0) + total

        for role in self.config.snapshot_data.userroles:
            tasks.append(asyncio.create_task(self._download(role)))

        await asyncio.gather(*tasks)

    async def _download(self, role_name):
        try:
            client = Userroles(self.config.authentication, self.config.org_name, role_name)

            users_resp = await run_blocking(client.list_users)
            users_path = self.full_path(f"userroles/{role_name}/users.json")
            await run_blocking(write_content_to_file, users_resp.json(), users_path, 2)

        except HTTPError as e:
            if e.response.status_code == 404:
                self.handle_http_error(e, f" for UserRole users ({role_name})")
                return
            raise

        try:
            perms_client = Permissions(self.config.authentication, self.config.org_name, role_name)

            perms_resp = await run_blocking(perms_client.get)
            perms = perms_resp.json()

            perms = Userroles.sort_resource_permissions(perms)

            perms_path = self.full_path(f"userroles/{role_name}/resource_permissions.json")

            await run_blocking(
              write_content_to_file,
              json.dumps(perms, indent=2),
              perms_path,
              2,
            )

        except HTTPError as e:
            if e.response.status_code == 404:
                self.handle_http_error(e, f" for UserRole permissions ({role_name})")
                return
            raise

        except Exception as e:
            self.handle_error(e, role_name)
            return

        self.progress("UserRoles")
