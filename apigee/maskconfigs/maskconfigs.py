import json

from requests.exceptions import HTTPError

import apigee.request
from apigee import APIGEE_ADMIN_API_URL, console
from apigee.utils import read_file_content

MASKCONFIGS_PATH = "/v1/organizations/{org}/apis/{api}/maskconfigs"
MASKCONFIG_PATH = "/v1/organizations/{org}/apis/{api}/maskconfigs/{name}"
ORG_MASKCONFIGS_PATH = "/v1/organizations/{org}/maskconfigs"


class Maskconfigs:

    def __init__(self, auth_config, org, api=None):
        self.auth = auth_config
        self.org = org
        self.api = api

    def _base(self):
        return MASKCONFIGS_PATH.format(org=self.org, api=self.api)

    def create(self, body):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{self._base()}",
          self.auth,
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def delete(self, name):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{MASKCONFIG_PATH.format(org=self.org, api=self.api, name=name)}",
          self.auth,
        )

    def get(self, name):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{MASKCONFIG_PATH.format(org=self.org, api=self.api, name=name)}",
          self.auth,
        )

    def list(self):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{self._base()}",
          self.auth,
        )

    def list_org(self):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{ORG_MASKCONFIGS_PATH.format(org=self.org)}",
          self.auth,
        )

    def push(self, file):
        data = read_file_content(file, type="json")
        name = data["name"]

        try:
            self.get(name)
            console.echo(f"Updating {name} for {self.api}")
        except HTTPError as e:
            if e.response.status_code != 404:
                raise
            console.echo(f"Creating {name} for {self.api}")

        console.echo(self.create(json.dumps(data)).text)
