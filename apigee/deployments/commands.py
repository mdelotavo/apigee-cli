import click
from click_aliases import ClickAliasedGroup

from apigee import console
from apigee.auth import common_auth_options, generate_authentication
from apigee.deployments.deployments import Deployments
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


@click.group(
  help="View API proxy and shared flow deployments.",
  cls=ClickAliasedGroup,
)
def deployments():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name):
    return Deployments(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


# --------------------
# API proxy
# --------------------
@deployments.command(
  help="Get API proxy deployment details.",
  aliases=["get-api-proxy-deployment-details"],
)
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
@click.option("--revision-name-only/--no-revision-name-only", "-r/-R", default=False)
def get(username, password, mfa_secret, token, zonename, org, profile, name, format, showindex, tablefmt, revision_name_only, **_):
    console.echo(
      _client(username, password, mfa_secret, token, zonename, org, name).get_api_proxy_deployment_details(
        formatted=True,
        format=format,
        showindex=showindex,
        tablefmt=tablefmt,
        revision_name_only=revision_name_only,
      )
    )


# --------------------
# Shared flow
# --------------------
@deployments.command(help="Get shared flow deployment details.")
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
@click.option("--revision-name-only/--no-revision-name-only", "-r/-R", default=False)
def get_shared_flow(
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
  revision_name_only,
  **_,
):
    console.echo(
      _client(username, password, mfa_secret, token, zonename, org, name).get_shared_flow_deployment_details(
        formatted=True,
        format=format,
        showindex=showindex,
        tablefmt=tablefmt,
        revision_name_only=revision_name_only,
      )
    )
