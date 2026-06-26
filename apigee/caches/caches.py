import json

from requests.exceptions import HTTPError

import apigee.request
from apigee import APIGEE_ADMIN_API_URL, console
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

    def clear(self, env):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{CLEAR_ALL_PATH.format(org=self.org, env=env, name=self.name)}",
          self.auth,
          params={"action": "clear"},
          headers={
            "Accept": "application/json",
            "Content-Type": "application/octet-stream",
          },
        )

    def clear_entry(self, env, entry):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{CLEAR_ENTRY_PATH.format(org=self.org, env=env, name=self.name, entry=entry)}",
          self.auth,
          params={"action": "clear"},
          headers={
            "Accept": "application/json",
            "Content-Type": "application/octet-stream",
          },
        )

    def create(self, env, body):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{CACHES_PATH.format(org=self.org, env=env)}",
          self.auth,
          params={"name": self.name},
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def delete(self, env):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{CACHE_PATH.format(org=self.org, env=env, name=self.name)}",
          self.auth,
        )

    def get(self, env):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{CACHE_PATH.format(org=self.org, env=env, name=self.name)}",
          self.auth,
        )

    def list(self, env, prefix=None, format="json"):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{CACHES_PATH.format(org=self.org, env=env)}",
          self.auth,
        )
        return CachesSerializer().serialize_details(resp, format, prefix=prefix)

    def update(self, env, body):
        return apigee.request.put(
          f"{APIGEE_ADMIN_API_URL}{CACHE_PATH.format(org=self.org, env=env, name=self.name)}",
          self.auth,
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
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
