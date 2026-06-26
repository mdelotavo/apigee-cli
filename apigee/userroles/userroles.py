import json

import apigee.request

from apigee import APIGEE_ADMIN_API_URL

ROLES_PATH = "/v1/organizations/{org}/userroles"
ROLE_PATH = "/v1/organizations/{org}/userroles/{role}"
USERS_PATH = "{base}/users"
PERMISSIONS_PATH = "{base}/permissions"
RESOURCE_PERMISSIONS_PATH = "{base}/resourcepermissions"


class Userroles:

    def __init__(self, auth_config, org, role=None):
        self.auth = auth_config
        self.org = org
        self.role = role

    def _base(self):
        return ROLE_PATH.format(org=self.org, role=self.role)

    # --------------------
    # roles
    # --------------------

    def create(self, roles):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{ROLES_PATH.format(org=self.org)}",
          self.auth,
          json={"role": [{
            "name": r
          } for r in roles]},
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def delete(self):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{self._base()}",
          self.auth,
          headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
          },
        )

    def list(self):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{ROLES_PATH.format(org=self.org)}",
          self.auth,
        )

    def get(self):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{self._base()}",
          self.auth,
        )

    # --------------------
    # users
    # --------------------

    def add_user(self, email):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{USERS_PATH.format(base=self._base())}",
          self.auth,
          params={"id": email},
          headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
          },
        )

    def remove_user(self, email):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{self._base()}/users/{email}",
          self.auth,
        )

    def list_users(self):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{USERS_PATH.format(base=self._base())}",
          self.auth,
        )

    def verify_user(self, email):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{self._base()}/users/{email}",
          self.auth,
        )

    # --------------------
    # permissions
    # --------------------

    def add_permissions(self, body):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{RESOURCE_PERMISSIONS_PATH.format(base=self._base())}",
          self.auth,
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def get_permissions(self, path=None):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{PERMISSIONS_PATH.format(base=self._base())}",
          self.auth,
          params={"path": path} if path else None,
        )

    def delete_permission(self, permission, path):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{self._base()}/permissions/{permission}",
          self.auth,
          params={"path": path},
          headers={
            "Accept": "application/json",
            "Content-Type": "application/octet-stream",
          },
        )

    def delete_resource_permissions(self, path):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{PERMISSIONS_PATH.format(base=self._base())}",
          self.auth,
          params={
            "path": path,
            "delete": "true",
          },
          headers={
            "Accept": "application/json",
            "Content-Type": "application/octet-stream",
          },
        )

    def verify_permission(self, permission, path):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{self._base()}/permissions/{permission}",
          self.auth,
          params={"path": path},
          headers={
            "Accept": "application/json",
            "Content-Type": "application/octet-stream",
          },
        )

    # --------------------
    # utilities
    # --------------------

    @staticmethod
    def sort_resource_permissions(data):
        for entry in data.get("resourcePermission", []):
            entry["permissions"].sort()
        return data
