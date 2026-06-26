import click
from click_option_group import RequiredMutuallyExclusiveOptionGroup, optgroup

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.prefix import common_prefix_options
from apigee.sharedflows.sharedflows import Sharedflows
from apigee.silent import common_silent_options
from apigee.verbose import common_verbose_options


@click.group(help="Manage shared flows.")
def sharedflows():
    pass


def _client(username, password, mfa_secret, token, zonename, org):
    return Sharedflows(generate_authentication(username, password, mfa_secret, token, zonename), org)


# --------------------
# basic
# --------------------


@sharedflows.command(help="List shared flows.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
def list(username, password, mfa_secret, token, zonename, org, profile, prefix, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list(prefix=prefix))


@sharedflows.command(help="Get shared flow details.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).get(name).text)


@sharedflows.command(help="List shared flow revisions.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
def revisions(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).revisions(name).text)


@sharedflows.command(help="View shared flow deployments.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
def deployments(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).deployments(name).text)


# --------------------
# import / export
# --------------------


@sharedflows.command(name="import", help="Import a shared flow.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-f", "--file", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option("-n", "--name", required=True)
def import_flow(username, password, mfa_secret, token, zonename, org, profile, file, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).import_flow(name, file).text)


@sharedflows.command(help="Export a shared flow revision.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-r", "--revision-number", type=click.INT, required=True)
@click.option("-O", "--output-file", default=None)
def export(username, password, mfa_secret, token, zonename, org, profile, name, revision_number, output_file, **_):
    _client(username, password, mfa_secret, token, zonename, org).export(
      name,
      revision_number,
      output=output_file or f"{name}.zip",
    )


# --------------------
# deployment
# --------------------


@sharedflows.command(help="Deploy a shared flow.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
@click.option("-n", "--name", required=True)
@optgroup.group("Deployment options", cls=RequiredMutuallyExclusiveOptionGroup)
@optgroup.option("-f", "--file", type=click.Path(exists=True, dir_okay=False))
@optgroup.option("-r", "--revision-number", type=click.INT)
@click.option("--override/--no-override", default=False)
@click.option("--delay", type=click.INT, default=0)
def deploy(
  username,
  password,
  mfa_secret,
  token,
  zonename,
  org,
  profile,
  environment,
  name,
  file,
  revision_number,
  override,
  delay,
  **_,
):
    console.echo(
      _client(username, password, mfa_secret, token, zonename, org).deploy(environment, name, revision_number, override=override, delay=delay, file=file).text
    )


@sharedflows.command(help="Undeploy a shared flow revision.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
@click.option("-n", "--name", required=True)
@click.option("-r", "--revision-number", type=click.INT, required=True)
def undeploy(username, password, mfa_secret, token, zonename, org, profile, environment, name, revision_number, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).undeploy(environment, name, revision_number).text)


# --------------------
# cleanup
# --------------------


@sharedflows.command(help="Delete undeployed revisions.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--save-last", type=click.INT, default=0)
@click.option("--dry-run/--no-dry-run", default=False)
def clean(username, password, mfa_secret, token, zonename, org, profile, name, save_last, dry_run, **_):
    _client(username, password, mfa_secret, token, zonename, org).delete_undeployed(
      name,
      save_last=save_last,
      dry_run=dry_run,
    )


# --------------------
# misc
# --------------------


@sharedflows.command(help="Get flow hook shared flow.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
@click.option("--flow-hook", required=True)
def flowhook(username, password, mfa_secret, token, zonename, org, profile, environment, flow_hook, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).flowhook(environment, flow_hook).text)
