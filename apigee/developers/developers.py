import json

import apigee.request

from apigee import APIGEE_ADMIN_API_URL
from apigee.developers.serializer import DevelopersSerializer

DEVELOPERS_PATH = "/v1/organizations/{org}/developers"
DEVELOPER_PATH = "/v1/organizations/{org}/developers/{dev}"
DEVELOPER_ATTR_PATH = "/v1/organizations/{org}/developers/{dev}/attributes/{attr}"
DEVELOPER_ATTRS_PATH = "/v1/organizations/{org}/developers/{dev}/attributes"


class Developers:

    def __init__(self, auth_config, org, dev=None):
        self.auth = auth_config
        self.org = org
        self.dev = dev

    def create(self, first_name, last_name, username, attributes='{"attributes": []}'):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPERS_PATH.format(org=self.org)}",
          self.auth,
          json={
            "email": self.dev,
            "firstName": first_name,
            "lastName": last_name,
            "userName": username,
            "attributes": json.loads(attributes)["attributes"],
          },
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def get(self):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPER_PATH.format(org=self.org, dev=self.dev)}",
          self.auth,
        )

    def delete(self):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPER_PATH.format(org=self.org, dev=self.dev)}",
          self.auth,
        )

    def list(self, prefix=None, expand=False, count=1000, startkey="", format="json"):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPERS_PATH.format(org=self.org)}",
          self.auth,
          params={
            "expand": expand,
            "count": count,
            "startKey": startkey,
          },
        )

        return DevelopersSerializer().serialize_details(resp, format, prefix=prefix)

    def get_by_app(self, app_name):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPERS_PATH.format(org=self.org)}",
          self.auth,
          params={"app": app_name},
        )

    def update(self, body):
        return apigee.request.put(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPER_PATH.format(org=self.org, dev=self.dev)}",
          self.auth,
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def set_status(self, action):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPER_PATH.format(org=self.org, dev=self.dev)}",
          self.auth,
          params={"action": action},
          headers={
            "Accept": "application/json",
            "Content-Type": "application/octet-stream",
          },
        )

    def get_attr(self, name):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPER_ATTR_PATH.format(org=self.org, dev=self.dev, attr=name)}",
          self.auth,
        )

    def get_attrs(self):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPER_ATTRS_PATH.format(org=self.org, dev=self.dev)}",
          self.auth,
        )

    def update_attr(self, name, value):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPER_ATTR_PATH.format(org=self.org, dev=self.dev, attr=name)}",
          self.auth,
          json={"value": value},
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def update_attrs(self, body):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPER_ATTRS_PATH.format(org=self.org, dev=self.dev)}",
          self.auth,
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def delete_attr(self, name):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{DEVELOPER_ATTR_PATH.format(org=self.org, dev=self.dev, attr=name)}",
          self.auth,
        )
