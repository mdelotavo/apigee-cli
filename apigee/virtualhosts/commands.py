import click

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.verbose import common_verbose_options
from apigee.virtualhosts.virtualhosts import Virtualhosts


@click.group(help="Manage virtual hosts.")
def virtualhosts():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return Virtualhosts(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


@virtualhosts.command(help="List virtual hosts.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
def list(username, password, mfa_secret, token, zonename, org, profile, environment, prefix, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list(environment, prefix=prefix))


@virtualhosts.command(help="Get a virtual host.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, environment, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get(environment).text)
