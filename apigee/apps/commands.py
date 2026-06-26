import click
from click_option_group import MutuallyExclusiveOptionGroup, optgroup

from apigee import console
from apigee.apps.apps import Apps
from apigee.auth import common_auth_options, generate_authentication
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.verbose import common_verbose_options


@click.group(help="Manage developer apps.")
def apps():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return Apps(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--developer", required=True)
@click.option("-b", "--body", required=True)
def create(username, password, mfa_secret, token, zonename, org, profile, name, developer, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).create(developer, body).text)


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--developer", required=True)
def delete(username, password, mfa_secret, token, zonename, org, profile, name, developer, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete(developer).text)


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--developer", required=True)
@click.option("--display-name", default=None)
@click.option("--callback-url", default=None)
def create_empty(username, password, mfa_secret, token, zonename, org, profile, name, developer, display_name, callback_url, **_):
    console.echo(
      _client(username, password, mfa_secret, token, zonename, org, name).create_empty(developer, display_name=display_name, callback_url=callback_url).text
    )


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--developer", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, developer, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get(developer).text)


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("--apptype", default=None)
@click.option("--expand", is_flag=True)
@click.option("--rows", type=int)
@click.option("--startkey", default=None)
@click.option("--status", default=None)
def list_org_apps(username, password, mfa_secret, token, zonename, org, profile, apptype, expand, rows, startkey, status, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list_org(apptype, expand, rows, startkey, status).text)


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
def get_org_app(username, password, mfa_secret, token, zonename, org, profile, name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get_org().text)


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@common_prefix_options
@click.option("--developer", required=True)
@click.option("--expand/--no-expand", default=False)
@click.option("--count", type=int, default=1000, show_default=True)
@click.option("--startkey", default="", show_default=True)
def list(username, password, mfa_secret, token, zonename, org, profile, developer, prefix, expand, count, startkey, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list(developer, prefix=prefix, expand=expand, count=count, startkey=startkey))


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--developer", required=True)
@click.option("--consumer-key", required=True)
def delete_creds(username, password, mfa_secret, token, zonename, org, profile, name, developer, consumer_key, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete_key(developer, consumer_key).text)


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--developer", required=True)
@click.option("--consumer-key", required=True)
@click.option("--action", default="approve", hidden=True)
def approve_creds(username, password, mfa_secret, token, zonename, org, profile, name, developer, consumer_key, action, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).update_key(developer, consumer_key, action).text)


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--developer", required=True)
@click.option("--consumer-key", required=True)
@click.option("--action", default="revoke", hidden=True)
def revoke_creds(username, password, mfa_secret, token, zonename, org, profile, name, developer, consumer_key, action, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).update_key(developer, consumer_key, action).text)


@apps.command()
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("-n", "--name", required=True)
@click.option("--developer", required=True)
@optgroup.group("consumerKey options", cls=MutuallyExclusiveOptionGroup)
@optgroup.option("--consumer-key", default=None)
@optgroup.option("--key-length", type=int, default=32, show_default=True)
@optgroup.group("consumerSecret options", cls=MutuallyExclusiveOptionGroup)
@optgroup.option("--consumer-secret", default=None)
@optgroup.option("--secret-length", type=int, default=32, show_default=True)
@click.option("--key-suffix", default=None)
@click.option("--key-delimiter", default="-")
@click.option("--products", multiple=True, default=[], show_default=True)
def create_creds(
  username,
  password,
  mfa_secret,
  token,
  zonename,
  org,
  profile,
  name,
  developer,
  consumer_key,
  key_length,
  consumer_secret,
  secret_length,
  key_suffix,
  key_delimiter,
  products,
  **_,
):
    console.echo(
      _client(username, password, mfa_secret, token, zonename, org, name).create_key(
        developer,
        key=consumer_key,
        secret=consumer_secret,
        key_len=key_length,
        sec_len=secret_length,
        suffix=key_suffix,
        products=products,
      ).text
    )


@apps.command()
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option(
  "-f",
  "--file",
  type=click.Path(exists=True, dir_okay=False, file_okay=True),
  required=True,
)
def restore(username, password, mfa_secret, token, zonename, org, profile, file, **_):
    _client(username, password, mfa_secret, token, zonename, org).restore(file)
