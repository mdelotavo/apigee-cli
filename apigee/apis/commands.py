import click
from click_option_group import MutuallyExclusiveOptionGroup, optgroup

from apigee import console
from apigee.apis.apis import Apis
from apigee.apis.deploy import deploy as deploy_tool
from apigee.apis.api_bundle_exporter import ApiBundleExporter
from apigee.auth import common_auth_options, generate_authentication
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.types import Struct
from apigee.verbose import common_verbose_options


@click.group(help="Operations on API proxies.")
def apis():
    pass


def _client(username, password, mfa_secret, token, zonename, org):
    return Apis(generate_authentication(username, password, mfa_secret, token, zonename), org)


@apis.command(help="Delete a revision of an API proxy.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-r", "--revision-number", type=int, required=True)
def delete_revision(username, password, mfa_secret, token, zonename, org, profile, name, revision_number, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).delete_api_proxy_revision(name, revision_number).text)


@apis.command(help="Deploy a revision of an API proxy.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-r", "--revision-number", type=int, required=True)
@click.option("--delay", type=int, default=0)
@click.option("--override/--no-override", default=False)
def deploy_revision(username, password, mfa_secret, token, zonename, org, profile, name, environment, revision_number, delay, override, **_):
    console.echo(
      _client(username, password, mfa_secret, token, zonename,
              org).deploy_api_proxy_revision(name, environment, revision_number, delay=delay, override=override).text
    )


@apis.command(help="Delete undeployed revisions.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--save-last", type=int, default=0)
@click.option("--dry-run/--no-dry-run", default=False)
def clean(username, password, mfa_secret, token, zonename, org, profile, name, save_last, dry_run, **_):
    _client(username, password, mfa_secret, token, zonename, org).delete_undeployed_revisions(name, save_last=save_last, dry_run=dry_run)


@apis.command(help="Delete an API proxy.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def delete(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    _client(username, password, mfa_secret, token, zonename, org).delete_api_proxy(name)


@apis.command(help="Export an API proxy revision.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-r", "--revision-number", type=int, required=True)
@click.option("-O", "--output-file", default=None)
def export(username, password, mfa_secret, token, zonename, org, profile, name, revision_number, output_file, **_):
    _client(username, password, mfa_secret, token, zonename, org).export_api_proxy(
      name,
      revision_number,
      write_to_filesystem=True,
      output_file=output_file or f"{name}.zip",
    )


@apis.command(help="Get an API proxy.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).get_api_proxy(name).text)


@apis.command(help="List API proxies.")
@common_auth_options
@common_verbose_options
@common_silent_options
@common_prefix_options
def list(username, password, mfa_secret, token, zonename, org, profile, prefix, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list_api_proxies(prefix=prefix))


@apis.command(help="List API proxy revisions.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def list_revisions(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list_api_proxy_revisions(name).text)


@apis.command(help="Undeploy an API proxy revision.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-r", "--revision-number", type=int, required=True)
def undeploy_revision(username, password, mfa_secret, token, zonename, org, profile, name, environment, revision_number, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).undeploy_api_proxy_revision(name, environment, revision_number).text)


@apis.command(help="Force undeploy an API proxy revision.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-r", "--revision-number", type=int, required=True)
def force_undeploy_revision(username, password, mfa_secret, token, zonename, org, profile, name, environment, revision_number, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).force_undeploy_api_proxy_revision(name, environment, revision_number).text)


@apis.command(help="Download API proxy with dependencies.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-r", "--revision-number", type=int, required=True)
@click.option("-e", "--environment", required=True)
@click.option("--work-tree")
@click.option("--force/--no-force", "-f/-F", default=False)
def pull(username, password, mfa_secret, token, zonename, org, profile, name, revision_number, environment, work_tree, force, **_):

    exporter = ApiBundleExporter(
      generate_authentication(username, password, mfa_secret, token, zonename),
      org,
      revision_number,
      environment,
      working_directory=work_tree,
    )

    exporter.export(name, force=force)


@apis.command(help="Deploy API from local bundle.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-e", "--environment", required=True)
@click.option("-n", "--name", required=True)
@click.option(
  "-d",
  "--directory",
  type=click.Path(exists=True, dir_okay=True, file_okay=False),
  required=True,
)
@optgroup.group("Deployment options", cls=MutuallyExclusiveOptionGroup)
@optgroup.option("--import-only/--no-import-only", "-i/-I", default=False)
@optgroup.option("--seamless-deploy/--no-seamless-deploy", "-s/-S", default=False)
def deploy(username, password, mfa_secret, token, zonename, org, profile, name, directory, import_only, seamless_deploy, environment, **_):
    deploy_tool(
      Struct(
        username=username,
        password=password,
        directory=directory,
        org=org,
        name=name,
        environment=environment,
        import_only=import_only,
        seamless_deploy=seamless_deploy,
        mfa_secret=mfa_secret,
        token=token,
        zonename=zonename,
      )
    )
