import click
from click_aliases import ClickAliasedGroup

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.permissions.permissions import Permissions
from apigee.silent import common_silent_options
from apigee.verbose import common_verbose_options

TABLEFMT_CHOICES = [
  "plain",
  "simple",
  "github",
  "grid",
  "fancy_grid",
  "pipe",
  "orgtbl",
  "jira",
  "presto",
  "psql",
  "rst",
  "mediawiki",
  "moinmoin",
  "youtrack",
  "html",
  "latex",
  "latex_raw",
  "latex_booktabs",
  "textile",
]


@click.group(help="Manage permissions for roles.", cls=ClickAliasedGroup)
def permissions():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name):
    return Permissions(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


# --------------------
# create
# --------------------


@permissions.command(help="Create permissions for a role.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-b", "--body", required=True)
def create(username, password, mfa_secret, token, zonename, org, profile, name, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).create(body).text)


@permissions.command(
  help="Create permissions using a template file.",
  aliases=["template-permissions"],
)
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
@click.option("--placeholder-key", default=None)
@click.option("--placeholder-value", default="", show_default=True)
def template(
  username,
  password,
  mfa_secret,
  token,
  zonename,
  org,
  profile,
  name,
  file,
  placeholder_key,
  placeholder_value,
  **_,
):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).apply_template(file, placeholder_key, placeholder_value).text)


# --------------------
# get
# --------------------


@permissions.command(help="Get permissions for a role.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option(
  "--format",
  default="table",
  type=click.Choice(["json", "table"], case_sensitive=False),
)
@click.option("--showindex/--no-showindex", default=False)
@click.option(
  "--tablefmt",
  type=click.Choice(TABLEFMT_CHOICES, case_sensitive=False),
  default="plain",
  show_default=True,
)
def get(
  username,
  password,
  mfa_secret,
  token,
  zonename,
  org,
  profile,
  name,
  format,
  showindex,
  tablefmt,
  **_,
):
    console.echo(
      _client(username, password, mfa_secret, token, zonename, org, name).get(
        formatted=True,
        format="text" if format == "json" else format,
        showindex=showindex,
        tablefmt=tablefmt,
      )
    )
