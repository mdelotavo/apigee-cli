import json
import requests

from apigee import APIGEE_ADMIN_API_URL, auth
from apigee.references.serializer import ReferencesSerializer

REFERENCES_PATH = "/v1/organizations/{org}/environments/{env}/references"
REFERENCE_PATH = "/v1/organizations/{org}/environments/{env}/references/{name}"


class References:

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

    def list(self, env, prefix=None, format="json"):
        resp = self._request(
          "get",
          REFERENCES_PATH.format(org=self.org, env=env),
        )
        return ReferencesSerializer().serialize_details(resp, format, prefix=prefix)

    def get(self, env):
        return self._request(
          "get",
          REFERENCE_PATH.format(org=self.org, env=env, name=self.name),
        )
