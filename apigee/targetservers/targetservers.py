import json
import requests
from requests.exceptions import HTTPError

from apigee import APIGEE_ADMIN_API_URL, auth, console
from apigee.targetservers.serializer import TargetserversSerializer
from apigee.utils import read_file_content

TARGETSERVERS_PATH = "/v1/organizations/{org}/environments/{env}/targetservers"
TARGETSERVER_PATH = "/v1/organizations/{org}/environments/{env}/targetservers/{name}"


class Targetservers:

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
        resp = requests.request(
          method,
          url,
          headers=self._headers(kwargs.pop("headers", None)),
          **kwargs,
        )
        resp.raise_for_status()
        return resp

    def _base(self, env):
        return TARGETSERVER_PATH.format(org=self.org, env=env, name=self.name)

    def create(self, env, body):
        return self._request(
          "post",
          TARGETSERVERS_PATH.format(org=self.org, env=env),
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def delete(self, env):
        return self._request("delete", self._base(env))

    def get(self, env):
        return self._request("get", self._base(env))

    def list(self, env, prefix=None, format="json"):
        resp = self._request(
          "get",
          TARGETSERVERS_PATH.format(org=self.org, env=env),
        )
        return TargetserversSerializer().serialize_details(resp, format, prefix=prefix)

    def update(self, env, body):
        return self._request(
          "put",
          self._base(env),
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def push(self, env, file):
        data = read_file_content(file, type="json")
        self.name = data["name"]

        try:
            self.get(env)
            console.echo(f"Updating {self.name}")
            resp = self.update(env, json.dumps(data))
        except HTTPError as e:
            if e.response.status_code != 404:
                raise
            console.echo(f"Creating {self.name}")
            resp = self.create(env, json.dumps(data))

        console.echo(resp.text)
        return resp
