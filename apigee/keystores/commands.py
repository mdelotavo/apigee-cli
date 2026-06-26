import click

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.keystores.keystores import Keystores
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.verbose import common_verbose_options


@click.group(help="Manage keystores and truststores.")
def keystores():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return Keystores(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


# --------------------
# keystores
# --------------------


@keystores.command(help="List keystores in an environment.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
def list(username, password, mfa_secret, token, zonename, org, profile, environment, prefix, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list(environment, prefix=prefix))


@keystores.command(help="Get a keystore.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, environment, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get(environment).text)


# --------------------
# certs
# --------------------


@keystores.command(help="List certs in a keystore.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def list_certs(username, password, mfa_secret, token, zonename, org, profile, name, environment, prefix, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).list_certs(environment, prefix=prefix))


@keystores.command(help="Get a cert.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("--cert-name", required=True)
@click.option("-e", "--environment", required=True)
def get_cert(username, password, mfa_secret, token, zonename, org, profile, name, environment, cert_name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get_cert(environment, cert_name).text)


@keystores.command(help="Export a cert.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("--cert-name", required=True)
@click.option("-e", "--environment", required=True)
def export(username, password, mfa_secret, token, zonename, org, profile, name, environment, cert_name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).export_cert(environment, cert_name).text)


# --------------------
# aliases
# --------------------


@keystores.command(help="List aliases.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def list_aliases(username, password, mfa_secret, token, zonename, org, profile, name, environment, prefix, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).list_aliases(environment, prefix=prefix))


@keystores.command(help="Get alias.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("--alias-name", required=True)
@click.option("-e", "--environment", required=True)
def get_alias(username, password, mfa_secret, token, zonename, org, profile, name, environment, alias_name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get_alias(environment, alias_name).text)


@keystores.command(help="Export certificate for alias.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("--alias-name", required=True)
@click.option("-e", "--environment", required=True)
def export_alias(username, password, mfa_secret, token, zonename, org, profile, name, environment, alias_name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).export_alias_cert(environment, alias_name).text)
