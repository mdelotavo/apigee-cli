import apigee.request

from apigee import APIGEE_ADMIN_API_URL
from apigee.virtualhosts.serializer import VirtualhostsSerializer

VIRTUALHOSTS_PATH = "/v1/o/{org}/environments/{env}/virtualhosts"
VIRTUALHOST_PATH = "/v1/o/{org}/environments/{env}/virtualhosts/{name}"


class Virtualhosts:

    def __init__(self, auth_config, org, name=None):
        self.auth = auth_config
        self.org = org
        self.name = name

    def _base(self, env):
        return VIRTUALHOST_PATH.format(org=self.org, env=env, name=self.name)

    def list(self, env, prefix=None, format="json"):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{VIRTUALHOSTS_PATH.format(org=self.org, env=env)}",
          self.auth,
        )

        return VirtualhostsSerializer().serialize_details(resp, format, prefix=prefix)

    def get(self, env):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{self._base(env)}",
          self.auth,
        )
