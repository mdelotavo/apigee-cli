import json
import requests

from apigee import APIGEE_ADMIN_API_URL, auth
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
        resp = requests.request(method, url, headers=self._headers(kwargs.pop("headers", None)), **kwargs)
        resp.raise_for_status()
        return resp

    def create(self, first_name, last_name, username, attributes='{"attributes": []}'):
        return self._request(
          "post",
          DEVELOPERS_PATH.format(org=self.org),
          headers={"Content-Type": "application/json"},
          json={
            "email": self.dev,
            "firstName": first_name,
            "lastName": last_name,
            "userName": username,
            "attributes": json.loads(attributes)["attributes"],
          },
        )

    def get(self):
        return self._request("get", DEVELOPER_PATH.format(org=self.org, dev=self.dev))

    def delete(self):
        return self._request("delete", DEVELOPER_PATH.format(org=self.org, dev=self.dev))

    def list(self, prefix=None, expand=False, count=1000, startkey="", format="json"):
        resp = self._request(
          "get",
          DEVELOPERS_PATH.format(org=self.org),
          params={
            "expand": expand,
            "count": count,
            "startKey": startkey
          },
        )
        return DevelopersSerializer().serialize_details(resp, format, prefix=prefix)

    def get_by_app(self, app_name):
        return self._request(
          "get",
          DEVELOPERS_PATH.format(org=self.org),
          params={"app": app_name},
        )

    def update(self, body):
        return self._request(
          "put",
          DEVELOPER_PATH.format(org=self.org, dev=self.dev),
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def set_status(self, action):
        return self._request(
          "post",
          DEVELOPER_PATH.format(org=self.org, dev=self.dev),
          params={"action": action},
          headers={"Content-Type": "application/octet-stream"},
        )

    def get_attr(self, name):
        return self._request("get", DEVELOPER_ATTR_PATH.format(org=self.org, dev=self.dev, attr=name))

    def get_attrs(self):
        return self._request("get", DEVELOPER_ATTRS_PATH.format(org=self.org, dev=self.dev))

    def update_attr(self, name, value):
        return self._request(
          "post",
          DEVELOPER_ATTR_PATH.format(org=self.org, dev=self.dev, attr=name),
          json={"value": value},
        )

    def update_attrs(self, body):
        return self._request(
          "post",
          DEVELOPER_ATTRS_PATH.format(org=self.org, dev=self.dev),
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def delete_attr(self, name):
        return self._request(
          "delete",
          DEVELOPER_ATTR_PATH.format(org=self.org, dev=self.dev, attr=name),
        )
