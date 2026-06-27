import click

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.developers.developers import Developers
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.verbose import common_verbose_options


@click.group(help="Manage developers.")
def developers():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return Developers(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--first-name", required=True)
@click.option("--last-name", required=True)
@click.option("--user-name", required=True)
@click.option("--attributes", default='{"attributes": []}')
def create(username, password, mfa_secret, token, zonename, org, profile, name, first_name, last_name, user_name, attributes, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).create(first_name, last_name, user_name, attributes=attributes).text)


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def delete(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete().text)


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get().text)


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("--app-name", required=True)
def get_by_app(username, password, mfa_secret, token, zonename, org, profile, app_name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).get_by_app(app_name).text)


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@common_prefix_options
@click.option("--expand/--no-expand", default=False)
@click.option("--count", type=int, default=1000, show_default=True)
@click.option("--startkey", default="", show_default=True)
def list(username, password, mfa_secret, token, zonename, org, profile, prefix, expand, count, startkey, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list(prefix=prefix, expand=expand, count=count, startkey=startkey))


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--action", type=click.Choice(["active", "inactive"], case_sensitive=False), required=True)
def set_status(username, password, mfa_secret, token, zonename, org, profile, name, action, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).set_status(action).text)


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-b", "--body", required=True)
def update(username, password, mfa_secret, token, zonename, org, profile, name, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).update(body).text)


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--attribute-name", required=True)
@click.option("--updated-value", required=True)
def update_attr(username, password, mfa_secret, token, zonename, org, profile, name, attribute_name, updated_value, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).update_attr(attribute_name, updated_value).text)


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--attribute-name", required=True)
def delete_attr(username, password, mfa_secret, token, zonename, org, profile, name, attribute_name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete_attr(attribute_name).text)


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def get_attrs(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get_attrs().text)


@developers.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-b", "--body", required=True)
def update_all_attrs(username, password, mfa_secret, token, zonename, org, profile, name, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).update_attrs(body).text)
