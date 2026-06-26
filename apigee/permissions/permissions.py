import json
import requests

from apigee import APIGEE_ADMIN_API_URL, auth
from apigee.permissions.serializer import PermissionsSerializer

PERMISSIONS_PATH = "/v1/organizations/{org}/userroles/{role}/resourcepermissions"
GET_PERMISSIONS_PATH = "/v1/o/{org}/userroles/{role}/permissions"


class Permissions:

    def __init__(self, auth_config, org, role):
        self.auth = auth_config
        self.org = org
        self.role = role

    def _headers(self, extra=None):
        return auth.set_authentication_headers(
          self.auth,
          custom_headers={
            "Accept": "application/json",
            **(extra or {})
          },
        )

    def _request(self, method, path, **kwargs):
        url = f"{APIGEE_ADMIN_API_URL}{path}"
        resp = requests.request(
          method,
          url,
          headers=self._headers(kwargs.pop("headers", None)),
          **kwargs,
        )
        resp.raise_for_status()
        return resp

    # --------------------
    # core
    # --------------------

    def create(self, body):
        return self._request(
          "post",
          PERMISSIONS_PATH.format(org=self.org, role=self.role),
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def apply_template(self, file, placeholder_key=None, placeholder_value=""):
        data = json.loads(open(file).read())

        if placeholder_key:
            for rp in data.get("resourcePermission", []):
                rp["path"] = rp["path"].replace(placeholder_key, placeholder_value)

        return self._request(
          "post",
          PERMISSIONS_PATH.format(org=self.org, role=self.role),
          headers={"Content-Type": "application/json"},
          json=data,
        )

    def get(self, formatted=False, format="text", showindex=False, tablefmt="plain"):
        resp = self._request(
          "get",
          GET_PERMISSIONS_PATH.format(org=self.org, role=self.role),
        )

        if not formatted:
            return resp

        return PermissionsSerializer().serialize_details(
          resp,
          format,
          showindex=showindex,
          tablefmt=tablefmt,
        )
