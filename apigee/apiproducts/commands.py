import click

from apigee import console
from apigee.apiproducts.apiproducts import Apiproducts
from apigee.auth import common_auth_options, generate_authentication
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.verbose import common_verbose_options


@click.group(help="API products management.")
def apiproducts():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return Apiproducts(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


@apiproducts.command(help="Create an API product.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-b", "--body", required=True)
def create(username, password, mfa_secret, token, zonename, org, profile, name, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).create_api_product(body).text)


@apiproducts.command(help="Delete an API product.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def delete(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete_api_product().text)


@apiproducts.command(help="Get an API product.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get_api_product().text)


@apiproducts.command(help="List API products.")
@common_auth_options
@common_verbose_options
@common_silent_options
@common_prefix_options
@click.option("--expand/--no-expand", default=False)
@click.option("--count", type=int, default=1000, show_default=True)
@click.option("--startkey", default="", show_default=True)
def list(username, password, mfa_secret, token, zonename, org, profile, prefix, expand, count, startkey, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list_api_products(prefix=prefix, expand=expand, count=count, startkey=startkey))


@apiproducts.command(help="Update an API product.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-b", "--body", required=True)
def update(username, password, mfa_secret, token, zonename, org, profile, name, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).update_api_product(body).text)


@apiproducts.command(help="Push API product (create/update).")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option(
  "-f",
  "--file",
  type=click.Path(exists=True, dir_okay=False, file_okay=True),
  required=True,
)
def push(username, password, mfa_secret, token, zonename, org, profile, file, **_):
    _client(username, password, mfa_secret, token, zonename, org).push_apiproducts(file)
