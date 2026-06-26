import json
import requests

from apigee import APIGEE_ADMIN_API_URL, auth

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

    def _headers(self, content_type="application/json"):
        return auth.set_authentication_headers(
          self.auth,
          custom_headers={
            "Accept": "application/json",
            "Content-Type": content_type,
          },
        )

    def _request(self, method, path, content_type="application/json", **kwargs):
        url = f"{APIGEE_ADMIN_API_URL}{path}"
        resp = requests.request(
          method,
          url,
          headers=self._headers(content_type),
          **kwargs,
        )
        resp.raise_for_status()
        return resp

    def _base(self):
        return ROLE_PATH.format(org=self.org, role=self.role)

    # --------------------
    # roles
    # --------------------

    def create(self, roles):
        return self._request(
          "post",
          ROLES_PATH.format(org=self.org),
          json={"role": [{
            "name": r
          } for r in roles]},
        )

    def delete(self):
        return self._request(
          "delete",
          self._base(),
          content_type="application/x-www-form-urlencoded",
        )

    def list(self):
        return self._request("get", ROLES_PATH.format(org=self.org))

    def get(self):
        return self._request("get", self._base())

    # --------------------
    # users
    # --------------------

    def add_user(self, email):
        return self._request(
          "post",
          USERS_PATH.format(base=self._base()),
          content_type="application/x-www-form-urlencoded",
          params={"id": email},
        )

    def remove_user(self, email):
        return self._request("delete", f"{self._base()}/users/{email}")

    def list_users(self):
        return self._request("get", USERS_PATH.format(base=self._base()))

    def verify_user(self, email):
        return self._request("get", f"{self._base()}/users/{email}")

    # --------------------
    # permissions
    # --------------------

    def add_permissions(self, body):
        return self._request(
          "post",
          RESOURCE_PERMISSIONS_PATH.format(base=self._base()),
          json=json.loads(body),
        )

    def get_permissions(self, path=None):
        return self._request(
          "get",
          PERMISSIONS_PATH.format(base=self._base()),
          params={"path": path} if path else None,
        )

    def delete_permission(self, permission, path):
        return self._request(
          "delete",
          f"{self._base()}/permissions/{permission}",
          content_type="application/octet-stream",
          params={"path": path},
        )

    def delete_resource_permissions(self, path):
        return self._request(
          "delete",
          PERMISSIONS_PATH.format(base=self._base()),
          content_type="application/octet-stream",
          params={
            "path": path,
            "delete": "true"
          },
        )

    def verify_permission(self, permission, path):
        return self._request(
          "get",
          f"{self._base()}/permissions/{permission}",
          content_type="application/octet-stream",
          params={"path": path},
        )

    # --------------------
    # utilities
    # --------------------

    @staticmethod
    def sort_resource_permissions(data):
        for entry in data.get("resourcePermission", []):
            entry["permissions"].sort()
        return data
