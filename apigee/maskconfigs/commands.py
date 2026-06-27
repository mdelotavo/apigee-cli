import click

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.maskconfigs.maskconfigs import Maskconfigs
from apigee.silent import common_silent_options
from apigee.verbose import common_verbose_options


@click.group(help="Manage data masking configurations.")
def maskconfigs():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return Maskconfigs(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


@maskconfigs.command(help="Create a data mask for an API proxy.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-b", "--body", required=True)
def create_api(username, password, mfa_secret, token, zonename, org, profile, name, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).create(body).text)


@maskconfigs.command(help="Delete a data mask for an API proxy.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--maskconfig-name", required=True)
def delete_api(username, password, mfa_secret, token, zonename, org, profile, name, maskconfig_name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete(maskconfig_name).text)


@maskconfigs.command(help="Get data mask details for an API proxy.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--maskconfig-name", required=True)
def get_api(username, password, mfa_secret, token, zonename, org, profile, name, maskconfig_name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get(maskconfig_name).text)


@maskconfigs.command(help="List data masks for an API proxy.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def list_api(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).list().text)


@maskconfigs.command(help="List data masks for an organization.")
@common_auth_options
@common_verbose_options
@common_silent_options
def list(username, password, mfa_secret, token, zonename, org, profile, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list_org().text)


@maskconfigs.command(help="Push data mask config (create/update).")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option(
  "-f",
  "--file",
  type=click.Path(exists=True, dir_okay=False, file_okay=True),
  required=True,
)
def push(username, password, mfa_secret, token, zonename, org, profile, name, file, **_):
    _client(username, password, mfa_secret, token, zonename, org, name).push(file)
