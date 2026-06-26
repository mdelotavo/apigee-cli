import json

import requests
from requests.exceptions import HTTPError

from apigee import APIGEE_ADMIN_API_URL, auth, console
from apigee.caches.serializer import CachesSerializer
from apigee.utils import read_file_content

CLEAR_ALL_PATH = "/v1/organizations/{org}/environments/{env}/caches/{name}/entries"
CLEAR_ENTRY_PATH = "/v1/organizations/{org}/environments/{env}/caches/{name}/entries/{entry}"
CACHE_PATH = "/v1/organizations/{org}/environments/{env}/caches/{name}"
CACHES_PATH = "/v1/organizations/{org}/environments/{env}/caches"


class Caches:

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

    def clear(self, env):
        return self._request(
          "post",
          CLEAR_ALL_PATH.format(org=self.org, env=env, name=self.name),
          params={"action": "clear"},
          headers={"Content-Type": "application/octet-stream"},
        )

    def clear_entry(self, env, entry):
        return self._request(
          "post",
          CLEAR_ENTRY_PATH.format(org=self.org, env=env, name=self.name, entry=entry),
          params={"action": "clear"},
          headers={"Content-Type": "application/octet-stream"},
        )

    def create(self, env, body):
        return self._request(
          "post",
          CACHES_PATH.format(org=self.org, env=env),
          params={"name": self.name},
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def delete(self, env):
        return self._request(
          "delete",
          CACHE_PATH.format(org=self.org, env=env, name=self.name),
        )

    def get(self, env):
        return self._request(
          "get",
          CACHE_PATH.format(org=self.org, env=env, name=self.name),
        )

    def list(self, env, prefix=None, format="json"):
        resp = self._request(
          "get",
          CACHES_PATH.format(org=self.org, env=env),
        )
        return CachesSerializer().serialize_details(resp, format, prefix=prefix)

    def update(self, env, body):
        return self._request(
          "put",
          CACHE_PATH.format(org=self.org, env=env, name=self.name),
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def push(self, env, file):
        data = read_file_content(file, type="json")
        self.name = data["name"]

        try:
            self.get(env)
            console.echo(f"Updating {self.name}")
            console.echo(self.update(env, json.dumps(data)).text)
        except HTTPError as e:
            if e.response.status_code != 404:
                raise
            console.echo(f"Creating {self.name}")
            console.echo(self.create(env, json.dumps(data)).text)
