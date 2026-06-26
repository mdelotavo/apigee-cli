import requests
from requests.exceptions import HTTPError

from apigee import APIGEE_ADMIN_API_URL, auth, console
from apigee.deployments.deployments import Deployments
from apigee.sharedflows.serializer import SharedflowsSerializer
from apigee.utils import apply_function_on_iterable, merge_dict_values, write_content_to_zip

SHAREDFLOWS_PATH = "/v1/organizations/{org}/sharedflows"
SHAREDFLOW_PATH = "/v1/organizations/{org}/sharedflows/{name}"
REVISION_PATH = "/v1/organizations/{org}/sharedflows/{name}/revisions/{rev}"
DEPLOY_PATH = "/v1/organizations/{org}/environments/{env}/sharedflows/{name}/revisions/{rev}/deployments"
DEPLOYMENTS_PATH = "/v1/organizations/{org}/sharedflows/{name}/deployments"
REVISIONS_PATH = "/v1/organizations/{org}/sharedflows/{name}/revisions"
FLOWHOOK_PATH = "/v1/organizations/{org}/environments/{env}/flowhooks/{hook}"
EXPORT_PATH = "/v1/organizations/{org}/sharedflows/{name}/revisions/{rev}"


class Sharedflows:

    def __init__(self, auth_config, org):
        self.auth = auth_config
        self.org = org

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

    # --------------------
    # basic
    # --------------------

    def list(self, prefix=None):
        resp = self._request("get", SHAREDFLOWS_PATH.format(org=self.org))
        return SharedflowsSerializer.serialize_details(resp, "json", prefix=prefix)

    def get(self, name):
        return self._request("get", SHAREDFLOW_PATH.format(org=self.org, name=name))

    def revisions(self, name):
        return self._request("get", REVISIONS_PATH.format(org=self.org, name=name))

    def deployments(self, name):
        return self._request("get", DEPLOYMENTS_PATH.format(org=self.org, name=name))

    def delete_revision(self, name, rev):
        return self._request("delete", REVISION_PATH.format(org=self.org, name=name, rev=rev))

    # --------------------
    # import / export
    # --------------------

    def import_flow(self, name, file):
        with open(file, "rb") as f:
            return self._request(
              "post",
              SHAREDFLOWS_PATH.format(org=self.org),
              headers={"Content-Type": "multipart/form-data"},
              files={"file": ("sharedflow.zip", f)},
              params={
                "action": "import",
                "name": name
              },
            )

    def export(self, name, rev, output=None, write=True):
        resp = self._request(
          "get",
          EXPORT_PATH.format(org=self.org, name=name, rev=rev),
          params={"format": "bundle"},
        )

        if write and output:
            write_content_to_zip(output, resp.content)

        return resp

    # --------------------
    # deployment
    # --------------------

    def deploy(self, env, name, rev, override=False, delay=0, file=None):
        existing = False

        try:
            self.revisions(name)
            existing = True
        except HTTPError as e:
            if e.response.status_code != 404:
                raise

        if file:
            rev = int(self.import_flow(name, file).json()["revision"])

        console.echo(f"Deploying revision {rev}... ", line_ending="", should_flush=True)

        resp = self._request(
          "post",
          DEPLOY_PATH.format(org=self.org, env=env, name=name, rev=rev),
          params=merge_dict_values({
            "override": "true" if override else "false",
            "delay": str(delay),
          }),
        )

        console.echo("Done")

        if existing:
            self.undeploy_others(env, name, keep={rev})

        return resp

    def undeploy(self, env, name, rev):
        return self._request("delete", DEPLOY_PATH.format(org=self.org, env=env, name=name, rev=rev))

    def undeploy_others(self, env, name, keep=set()):
        resp = self.deployments(name)

        for env_data in resp.json().get("environment", []):
            if env_data["name"] == env:
                for r in env_data.get("revision", []):
                    revision = int(r["name"])

                    if revision not in keep:
                        console.echo(f"Undeploying revision {revision}... ", line_ending="", should_flush=True)
                        self.undeploy(env, name, revision)
                        console.echo("Done")

        return resp

    # --------------------
    # cleanup
    # --------------------

    def delete_undeployed(self, name, save_last=0, dry_run=False):
        deployed = SharedflowsSerializer.filter_deployment_details(Deployments(self.auth, self.org, name).get_shared_flow_deployment_details().json())

        undeployed = SharedflowsSerializer.filter_undeployed_revisions(
          self.revisions(name).json(),
          SharedflowsSerializer.filter_deployed_revisions(deployed),
          save_last=save_last,
        )

        console.echo(f"Undeployed revisions to be deleted: {undeployed}")

        if dry_run:
            return undeployed

        def _delete(rev):
            console.echo(f"Deleting revision {rev}")
            self.delete_revision(name, rev)

        return apply_function_on_iterable(undeployed, _delete)

    # --------------------
    # misc
    # --------------------

    def flowhook(self, env, hook):
        return self._request("get", FLOWHOOK_PATH.format(org=self.org, env=env, hook=hook))
