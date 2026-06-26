import json
import requests
from requests.exceptions import HTTPError

from apigee import APIGEE_ADMIN_API_URL, auth, console
from apigee.utils import read_file_content

MASKCONFIGS_PATH = "/v1/organizations/{org}/apis/{api}/maskconfigs"
MASKCONFIG_PATH = "/v1/organizations/{org}/apis/{api}/maskconfigs/{name}"
ORG_MASKCONFIGS_PATH = "/v1/organizations/{org}/maskconfigs"


class Maskconfigs:

    def __init__(self, auth_config, org, api=None):
        self.auth = auth_config
        self.org = org
        self.api = api

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

    def _base(self):
        return MASKCONFIGS_PATH.format(org=self.org, api=self.api)

    def create(self, body):
        return self._request(
          "post",
          self._base(),
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def delete(self, name):
        return self._request(
          "delete",
          MASKCONFIG_PATH.format(org=self.org, api=self.api, name=name),
        )

    def get(self, name):
        return self._request(
          "get",
          MASKCONFIG_PATH.format(org=self.org, api=self.api, name=name),
        )

    def list(self):
        return self._request("get", self._base())

    def list_org(self):
        return self._request("get", ORG_MASKCONFIGS_PATH.format(org=self.org))

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
