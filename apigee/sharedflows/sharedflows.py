import apigee.request
from requests.exceptions import HTTPError

from apigee import APIGEE_ADMIN_API_URL, console
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

    # basic

    def list(self, prefix=None):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{SHAREDFLOWS_PATH.format(org=self.org)}",
          self.auth,
        )
        return SharedflowsSerializer.serialize_details(resp, "json", prefix=prefix)

    def get(self, name):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{SHAREDFLOW_PATH.format(org=self.org, name=name)}",
          self.auth,
        )

    def revisions(self, name):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{REVISIONS_PATH.format(org=self.org, name=name)}",
          self.auth,
        )

    def deployments(self, name):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{DEPLOYMENTS_PATH.format(org=self.org, name=name)}",
          self.auth,
        )

    def delete_revision(self, name, rev):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{REVISION_PATH.format(org=self.org, name=name, rev=rev)}",
          self.auth,
        )

    # import / export

    def import_flow(self, name, file):
        with open(file, "rb") as f:
            return apigee.request.post(
              f"{APIGEE_ADMIN_API_URL}{SHAREDFLOWS_PATH.format(org=self.org)}",
              self.auth,
              files={"file": ("sharedflow.zip", f)},
              params={
                "action": "import",
                "name": name,
              },
              headers={
                "Accept": "application/json",
                "Content-Type": "multipart/form-data",
              },
            )

    def export(self, name, rev, output=None, write=True):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{EXPORT_PATH.format(org=self.org, name=name, rev=rev)}",
          self.auth,
          params={"format": "bundle"},
        )

        if write and output:
            write_content_to_zip(output, resp.content)

        return resp

    # deployment

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

        resp = apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{DEPLOY_PATH.format(org=self.org, env=env, name=name, rev=rev)}",
          self.auth,
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
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{DEPLOY_PATH.format(org=self.org, env=env, name=name, rev=rev)}",
          self.auth,
        )

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

    # cleanup

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

    # misc

    def flowhook(self, env, hook):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{FLOWHOOK_PATH.format(org=self.org, env=env, hook=hook)}",
          self.auth,
        )
