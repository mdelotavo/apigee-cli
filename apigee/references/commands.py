import click

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.prefix import common_prefix_options
from apigee.references.references import References
from apigee.silent import common_silent_options
from apigee.verbose import common_verbose_options


@click.group(help="Manage references.")
def references():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return References(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


@references.command(help="List references.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
def list(username, password, mfa_secret, token, zonename, org, profile, environment, prefix, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list(environment, prefix=prefix))


@references.command(help="Get a reference.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, environment, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get(environment).text)
