import click

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.targetservers.targetservers import Targetservers
from apigee.verbose import common_verbose_options


@click.group(help="Manage TargetServers.")
def targetservers():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return Targetservers(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


@targetservers.command(help="Create a TargetServer.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-b", "--body", required=True)
def create(username, password, mfa_secret, token, zonename, org, profile, name, environment, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).create(environment, body).text)


@targetservers.command(help="Delete a TargetServer.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def delete(username, password, mfa_secret, token, zonename, org, profile, name, environment, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete(environment).text)


@targetservers.command(help="List TargetServers.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
def list(username, password, mfa_secret, token, zonename, org, profile, environment, prefix, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list(environment, prefix=prefix))


@targetservers.command(help="Get a TargetServer.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, environment, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get(environment).text)


@targetservers.command(help="Update a TargetServer.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-b", "--body", required=True)
def update(username, password, mfa_secret, token, zonename, org, profile, name, environment, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).update(environment, body).text)


@targetservers.command(help="Push TargetServer (create/update).")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
@click.option(
  "-f",
  "--file",
  type=click.Path(exists=True, dir_okay=False, file_okay=True),
  required=True,
)
def push(username, password, mfa_secret, token, zonename, org, profile, environment, file, **_):
    _client(username, password, mfa_secret, token, zonename, org).push(environment, file)
