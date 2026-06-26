import click

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.silent import common_silent_options
from apigee.userroles.userroles import Userroles
from apigee.verbose import common_verbose_options


@click.group(help="Manage user roles.")
def userroles():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return Userroles(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


# --------------------
# roles
# --------------------


@userroles.command(help="Create user roles.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--names", multiple=True, required=True)
def create(username, password, mfa_secret, token, zonename, org, profile, names, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).create(names).text)


@userroles.command(help="Delete a role.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def delete(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete().text)


@userroles.command(help="Get a role.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get().text)


@userroles.command(help="List roles.")
@common_auth_options
@common_verbose_options
@common_silent_options
def list(username, password, mfa_secret, token, zonename, org, profile, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list().text)


# --------------------
# users
# --------------------


@userroles.command(help="Add a user to a role.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--user-email", required=True)
def add_user(username, password, mfa_secret, token, zonename, org, profile, name, user_email, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).add_user(user_email).text)


@userroles.command(help="Remove user from role.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--user-email", required=True)
def remove_user(username, password, mfa_secret, token, zonename, org, profile, name, user_email, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).remove_user(user_email).text)


@userroles.command(help="List users in a role.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def get_users(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).list_users().text)


@userroles.command(help="Verify user membership.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--user-email", required=True)
def verify_membership(username, password, mfa_secret, token, zonename, org, profile, name, user_email, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).verify_user(user_email).text)


# --------------------
# permissions
# --------------------


@userroles.command(help="Add permissions to a role.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("-b", "--body", required=True)
def add_permissions(username, password, mfa_secret, token, zonename, org, profile, name, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).add_permissions(body).text)


@userroles.command(help="Get permissions for a role.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--resource-path", default=None)
def get_permissions(username, password, mfa_secret, token, zonename, org, profile, name, resource_path, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get_permissions(resource_path).text)


@userroles.command(help="List permissions for a role.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def list_permissions(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get_permissions().text)


@userroles.command(help="Delete permission from resource.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--permission", required=True)
@click.option("--resource-path", required=True)
def delete_permission(username, password, mfa_secret, token, zonename, org, profile, name, permission, resource_path, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete_permission(permission, resource_path).text)


@userroles.command(help="Delete all permissions for a resource.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--resource-path", required=True)
def delete_resource(username, password, mfa_secret, token, zonename, org, profile, name, resource_path, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete_resource_permissions(resource_path).text)


@userroles.command(help="Verify role permission on a resource.")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--permission", required=True)
@click.option("--resource-path", required=True)
def verify_permission(username, password, mfa_secret, token, zonename, org, profile, name, permission, resource_path, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).verify_permission(permission, resource_path).text)
