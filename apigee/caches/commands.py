import click

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.caches.caches import Caches
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.verbose import common_verbose_options


@click.group(help="Manage environment-scoped caches.")
def caches():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return Caches(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


@caches.command(help="Clear all cache entries.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def clear(username, password, mfa_secret, token, zonename, org, profile, name, environment, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).clear(environment).text)


@caches.command(help="Clear a cache entry.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--entry", required=True)
def clear_entry(username, password, mfa_secret, token, zonename, org, profile, name, environment, entry, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).clear_entry(environment, entry).text)


@caches.command(help="Create a cache.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-b", "--body", required=True)
def create(username, password, mfa_secret, token, zonename, org, profile, name, environment, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).create(environment, body).text)


@caches.command(help="Get cache details.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, environment, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get(environment).text)


@caches.command(help="List caches.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
def list(username, password, mfa_secret, token, zonename, org, profile, environment, prefix, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list(environment, prefix=prefix))


@caches.command(help="Update a cache.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-b", "--body", required=True)
def update(username, password, mfa_secret, token, zonename, org, profile, name, environment, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).update(environment, body).text)


@caches.command(help="Delete a cache.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def delete(username, password, mfa_secret, token, zonename, org, profile, name, environment, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete(environment).text)


@caches.command(help="Push cache (create/update).")
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
