import requests

from apigee import APIGEE_ADMIN_API_URL, auth, console
from apigee.apis.serializer import ApisSerializer
from apigee.deployments.deployments import Deployments
from apigee.utils import apply_function_on_iterable, write_content_to_zip


DELETE_API_PROXY_PATH = "/v1/organizations/{org}/apis/{api_name}"
DELETE_API_PROXY_REVISION_PATH = "/v1/organizations/{org}/apis/{api_name}/revisions/{revision_number}"
DEPLOY_API_PROXY_REVISION_PATH = "/v1/organizations/{org}/environments/{environment}/apis/{api_name}/revisions/{revision_number}/deployments"
EXPORT_API_PROXY_PATH = "/v1/organizations/{org}/apis/{api_name}/revisions/{revision_number}"
GET_API_PROXY_PATH = "/v1/organizations/{org}/apis/{api_name}"
LIST_API_PROXIES_PATH = "/v1/organizations/{org}/apis"
LIST_API_PROXY_REVISIONS_PATH = "/v1/organizations/{org}/apis/{api_name}/revisions"
UNDEPLOY_API_PROXY_REVISION_PATH = "/v1/organizations/{org}/environments/{environment}/apis/{api_name}/revisions/{revision_number}/deployments"
FORCE_UNDEPLOY_API_PROXY_REVISION_PATH = "/v1/organizations/{org}/apis/{api_name}/revisions/{revision_number}/deployments"


class Apis:

    def __init__(self, auth_config, org):
        self.auth = auth_config
        self.org = org

    def _headers(self, extra=None):
        return auth.set_authentication_headers(
            self.auth,
            custom_headers={"Accept": "application/json", **(extra or {})},
        )

    def _request(self, method, path, **kwargs):
        url = f"{APIGEE_ADMIN_API_URL}{path}"
        resp = requests.request(method, url, headers=self._headers(kwargs.pop("headers", None)), **kwargs)
        resp.raise_for_status()
        return resp

    def delete_api_proxy(self, name):
        return self._request("delete", DELETE_API_PROXY_PATH.format(org=self.org, api_name=name))

    def delete_api_proxy_revision(self, name, revision):
        return self._request(
            "delete",
            DELETE_API_PROXY_REVISION_PATH.format(org=self.org, api_name=name, revision_number=revision),
        )

    def delete_undeployed_revisions(self, name, save_last=0, dry_run=False):
        details = Deployments(self.auth, self.org, name).get_api_proxy_deployment_details().json()
        deployed = ApisSerializer.filter_deployed_revisions(
            ApisSerializer.filter_deployment_details(details)
        )
        revisions = self.list_api_proxy_revisions(name).json()

        undeployed = ApisSerializer.filter_undeployed_revisions(revisions, deployed, save_last=save_last)
        console.echo(f"Undeployed revisions to be deleted: {undeployed}")

        if dry_run:
            return undeployed

        return apply_function_on_iterable(
            undeployed,
            lambda r: (
                console.echo(f"Deleting revision {r}"),
                self.delete_api_proxy_revision(name, r),
            ),
        )

    def deploy_api_proxy_revision(self, name, env, revision, delay=0, override=False):
        return self._request(
            "post",
            DEPLOY_API_PROXY_REVISION_PATH.format(
                org=self.org, environment=env, api_name=name, revision_number=revision
            ) + f"?delay={delay}",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"override": "true" if override else "false"},
        )

    def export_api_proxy(self, name, revision, write_to_filesystem=True, output_file=None):
        resp = self._request(
            "get",
            EXPORT_API_PROXY_PATH.format(org=self.org, api_name=name, revision_number=revision),
            params={"format": "bundle"},
        )

        if write_to_filesystem:
            write_content_to_zip(output_file, resp.content)

        return resp

    def force_undeploy_api_proxy_revision(self, name, env, revision):
        return self._request(
            "post",
            FORCE_UNDEPLOY_API_PROXY_REVISION_PATH.format(
                org=self.org, api_name=name, revision_number=revision
            ),
            params={"action": "undeploy", "env": env, "force": "true"},
        )

    def undeploy_api_proxy_revision(self, name, env, revision):
        return self._request(
            "delete",
            UNDEPLOY_API_PROXY_REVISION_PATH.format(
                org=self.org, environment=env, api_name=name, revision_number=revision
            ),
        )

    def get_api_proxy(self, name):
        return self._request(
            "get",
            GET_API_PROXY_PATH.format(org=self.org, api_name=name),
        )

    def list_api_proxies(self, prefix=None, format="json"):
        resp = self._request(
            "get",
            LIST_API_PROXIES_PATH.format(org=self.org),
        )
        return ApisSerializer.serialize_details(resp, format, prefix=prefix)

    def list_api_proxy_revisions(self, name):
        return self._request(
            "get",
            LIST_API_PROXY_REVISIONS_PATH.format(org=self.org, api_name=name),
        )