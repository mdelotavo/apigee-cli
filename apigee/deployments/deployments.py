import apigee.request

from apigee import APIGEE_ADMIN_API_URL
from apigee.deployments.serializer import DeploymentsSerializer

API_PROXY_PATH = "/v1/organizations/{org}/apis/{name}/deployments"
SHARED_FLOW_PATH = "/v1/organizations/{org}/sharedflows/{name}/deployments"


class Deployments:

    def __init__(self, auth_config, org, name):
        self.auth = auth_config
        self.org = org
        self.name = name

    def _format(self, resp, formatted, format, showindex, tablefmt, revision_only):
        if not formatted:
            return resp

        if revision_only:
            return DeploymentsSerializer().serialize_details(
              resp,
              format,
              showindex=showindex,
              tablefmt=tablefmt,
            )

        return DeploymentsSerializer().serialize_details(resp, "text")

    def get_api_proxy_deployment_details(
      self,
      formatted=False,
      format="text",
      showindex=False,
      tablefmt="plain",
      revision_name_only=False,
    ):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{API_PROXY_PATH.format(org=self.org, name=self.name)}",
          self.auth,
        )

        return self._format(resp, formatted, format, showindex, tablefmt, revision_name_only)

    def get_shared_flow_deployment_details(
      self,
      formatted=False,
      format="text",
      showindex=False,
      tablefmt="plain",
      revision_name_only=False,
    ):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{SHARED_FLOW_PATH.format(org=self.org, name=self.name)}",
          self.auth,
        )

        return self._format(resp, formatted, format, showindex, tablefmt, revision_name_only)
