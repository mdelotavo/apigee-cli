import json
from requests.exceptions import HTTPError

import apigee.request
from apigee import APIGEE_ADMIN_API_URL, console
from apigee.targetservers.serializer import TargetserversSerializer
from apigee.utils import read_file_content

TARGETSERVERS_PATH = "/v1/organizations/{org}/environments/{env}/targetservers"
TARGETSERVER_PATH = "/v1/organizations/{org}/environments/{env}/targetservers/{name}"


class Targetservers:

    def __init__(self, auth_config, org, name=None):
        self.auth = auth_config
        self.org = org
        self.name = name

    def _base(self, env):
        return TARGETSERVER_PATH.format(org=self.org, env=env, name=self.name)

    def create(self, env, body):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{TARGETSERVERS_PATH.format(org=self.org, env=env)}",
          self.auth,
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def delete(self, env):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{self._base(env)}",
          self.auth,
        )

    def get(self, env):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{self._base(env)}",
          self.auth,
        )

    def list(self, env, prefix=None, format="json"):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{TARGETSERVERS_PATH.format(org=self.org, env=env)}",
          self.auth,
        )
        return TargetserversSerializer().serialize_details(resp, format, prefix=prefix)

    def update(self, env, body):
        return apigee.request.put(
          f"{APIGEE_ADMIN_API_URL}{self._base(env)}",
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
            resp = self.update(env, json.dumps(data))
        except HTTPError as e:
            if e.response.status_code != 404:
                raise
            console.echo(f"Creating {self.name}")
            resp = self.create(env, json.dumps(data))

        console.echo(resp.text)
        return resp
