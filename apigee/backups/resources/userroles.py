import asyncio
import json
from requests.exceptions import HTTPError

from apigee.userroles.userroles import Userroles
from apigee.permissions.permissions import Permissions
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class UserRolesBackup(BaseBackup):

    async def snapshot(self):
        roles = await run_blocking(Userroles(self.config.authentication, self.config.org_name, None).list_user_roles)

        roles = roles.json()

        if self.config.prefix:
            roles = [r for r in roles if r.startswith(self.config.prefix)]

        return roles

    def save_snapshot(self, data):
        self.config.snapshot_data.userroles = data

        path = self.full_path("snapshots/userroles/userroles.json")
        write_content_to_file(data, path, indentation=2)

    async def download(self):
        tasks = [self._download(role) for role in self.config.snapshot_data.userroles]
        await asyncio.gather(*tasks)

    async def _download(self, role_name):
        try:
            # users for role
            users = await run_blocking(Userroles(self.config.authentication, self.config.org_name, role_name).get_users_for_a_role)

            users_path = self.full_path(f"userroles/{role_name}/users.json")
            await run_blocking(write_content_to_file, users.json(), users_path, 2)

        except HTTPError as e:
            self.handle_http_error(e, f" for UserRole users ({role_name})")

        try:
            # permissions
            perms = await run_blocking(
              Permissions(self.config.authentication, self.config.org_name, role_name).get_permissions,
              True,
              "json",
            )

            perms = Userroles.sort_resource_permissions(perms)

            perms_path = self.full_path(f"userroles/{role_name}/resource_permissions.json")

            await run_blocking(
              write_content_to_file,
              json.dumps(perms, indent=2),
              perms_path,
              2,
            )

        except HTTPError as e:
            self.handle_http_error(e, f" for UserRole permissions ({role_name})")
        except Exception as e:
            self.handle_error(e, role_name)

        self.progress("UserRoles")
