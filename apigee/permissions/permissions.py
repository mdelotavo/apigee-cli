import json

import apigee.request

from apigee import APIGEE_ADMIN_API_URL
from apigee.permissions.serializer import PermissionsSerializer

PERMISSIONS_PATH = "/v1/organizations/{org}/userroles/{role}/resourcepermissions"
GET_PERMISSIONS_PATH = "/v1/o/{org}/userroles/{role}/permissions"


class Permissions:

    def __init__(self, auth_config, org, role):
        self.auth = auth_config
        self.org = org
        self.role = role

    # --------------------
    # core
    # --------------------

    def create(self, body):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{PERMISSIONS_PATH.format(org=self.org, role=self.role)}",
          self.auth,
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def apply_template(self, file, placeholder_key=None, placeholder_value=""):
        data = json.loads(open(file).read())

        if placeholder_key:
            for rp in data.get("resourcePermission", []):
                rp["path"] = rp["path"].replace(placeholder_key, placeholder_value)

        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{PERMISSIONS_PATH.format(org=self.org, role=self.role)}",
          self.auth,
          json=data,
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def get(self, formatted=False, format="text", showindex=False, tablefmt="plain"):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{GET_PERMISSIONS_PATH.format(org=self.org, role=self.role)}",
          self.auth,
        )

        if not formatted:
            return resp

        return PermissionsSerializer().serialize_details(
          resp,
          format,
          showindex=showindex,
          tablefmt=tablefmt,
        )
