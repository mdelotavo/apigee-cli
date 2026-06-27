import apigee.request

from apigee import APIGEE_ADMIN_API_URL
from apigee.references.serializer import ReferencesSerializer

REFERENCES_PATH = "/v1/organizations/{org}/environments/{env}/references"
REFERENCE_PATH = "/v1/organizations/{org}/environments/{env}/references/{name}"


class References:

    def __init__(self, auth_config, org, name=None):
        self.auth = auth_config
        self.org = org
        self.name = name

    def list(self, env, prefix=None, format="json"):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{REFERENCES_PATH.format(org=self.org, env=env)}",
          self.auth,
        )

        return ReferencesSerializer().serialize_details(resp, format, prefix=prefix)

    def get(self, env):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{REFERENCE_PATH.format(org=self.org, env=env, name=self.name)}",
          self.auth,
        )
