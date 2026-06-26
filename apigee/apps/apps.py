import json
import random
import string

import requests

from apigee import APIGEE_ADMIN_API_URL, auth, console
from apigee.apps.serializer import AppsSerializer

GET_ORG_APP_PATH = "/v1/organizations/{org}/apps/{name}"
LIST_ORG_APPS_PATH = "/v1/organizations/{org}/apps"

DEV_APPS_PATH = "/v1/organizations/{org}/developers/{dev}/apps"
DEV_APP_PATH = "/v1/organizations/{org}/developers/{dev}/apps/{name}"
DEV_APP_KEYS_PATH = "/v1/organizations/{org}/developers/{dev}/apps/{name}/keys"
DEV_APP_KEY_PATH = "/v1/organizations/{org}/developers/{dev}/apps/{name}/keys/{key}"
CREATE_KEY_PATH = "/v1/organizations/{org}/developers/{dev}/apps/{name}/keys/create"


def _rand(n):
    return "".join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(n))


class Apps:

    def __init__(self, auth_config, org, name=None):
        self.auth = auth_config
        self.org = org
        self.name = name

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

    def get(self, dev):
        return self._request("get", DEV_APP_PATH.format(org=self.org, dev=dev, name=self.name))

    def get_org(self):
        return self._request("get", GET_ORG_APP_PATH.format(org=self.org, name=self.name))

    def delete(self, dev):
        return self._request("delete", DEV_APP_PATH.format(org=self.org, dev=dev, name=self.name))

    def create(self, dev, body):
        return self._request(
          "post",
          DEV_APPS_PATH.format(org=self.org, dev=dev),
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def create_empty(self, dev, display_name="", callback_url=""):
        body = {"name": self.name}

        if display_name:
            body["attributes"] = [{"name": "DisplayName", "value": display_name}]
        if callback_url:
            body["callbackUrl"] = callback_url

        resp = self._request(
          "post",
          DEV_APPS_PATH.format(org=self.org, dev=dev),
          headers={"Content-Type": "application/json"},
          json=body,
        )

        self.delete_key(dev, resp.json()["credentials"][0]["consumerKey"])
        return self.get(dev)

    def list(self, dev, prefix=None, expand=False, count=1000, startkey="", format="json"):
        params = {"expand": expand} if expand else {"count": count, "startKey": startkey}

        resp = self._request(
          "get",
          DEV_APPS_PATH.format(org=self.org, dev=dev),
          params=params,
        )

        return AppsSerializer().serialize_details(resp, format, prefix=prefix)

    def list_all(self, developers, **kwargs):
        return {d: self.list(d, **kwargs) for d in developers}

    def list_org(self, apptype=None, expand=False, rows=None, startkey=None, status=None):
        params = {}

        if apptype:
            params["apptype"] = apptype
        if expand:
            params["expand"] = "true"
        if rows:
            params["rows"] = rows
        if startkey:
            params["startKey"] = startkey
        if status:
            params["status"] = status

        return self._request("get", LIST_ORG_APPS_PATH.format(org=self.org), params=params)

    def create_key(self, dev, key=None, secret=None, products=None, key_len=32, sec_len=32, suffix=None):
        key = key or _rand(key_len)
        secret = secret or _rand(sec_len)

        if suffix:
            key = f"{key}-{suffix}"

        resp = self._request(
          "post",
          CREATE_KEY_PATH.format(org=self.org, dev=dev, name=self.name),
          headers={"Content-Type": "application/json"},
          json={
            "consumerKey": key,
            "consumerSecret": secret
          },
        )

        if products:
            data = resp.json()
            console.echo(resp.text)
            console.echo(f"Adding API Products {products} to consumerKey {data['consumerKey']}")

            return self.add_product(
              dev,
              data["consumerKey"],
              json.dumps({
                "apiProducts": products,
                "attributes": data.get("attributes")
              }),
            )

        return resp

    def add_product(self, dev, key, body):
        return self._request(
          "post",
          DEV_APP_KEY_PATH.format(org=self.org, dev=dev, name=self.name, key=key),
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def delete_key(self, dev, key):
        return self._request("delete", DEV_APP_KEY_PATH.format(org=self.org, dev=dev, name=self.name, key=key))

    def update_key(self, dev, key, action):
        return self._request(
          "post",
          DEV_APP_KEY_PATH.format(org=self.org, dev=dev, name=self.name, key=key),
          params={"action": action},
          headers={"Content-Type": "application/octet-stream"},
        )

    def restore(self, file):
        data = json.loads(open(file).read())
        self.name = data["name"]

        body = {
          "name": data["name"],
          "attributes": data.get("attributes"),
          "scopes": data.get("scopes"),
          "callbackUrl": data.get("callbackUrl"),
        }

        body = {k: v for k, v in body.items() if v}

        resp = self.create(data["developerId"], json.dumps(body))
        key = resp.json()["credentials"][0]["consumerKey"]
        self.delete_key(data["developerId"], key)

        for cred in data.get("credentials", []):
            self.create_key(
              data["developerId"],
              key=cred["consumerKey"],
              secret=cred["consumerSecret"],
              products=[p["apiproduct"] for p in cred.get("apiProducts", [])],
            )

        return self.get(data["developerId"])
