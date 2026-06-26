import asyncio
import click

from apigee.auth import common_auth_options, generate_authentication
from apigee.backups import BackupConfig, BackupRunner
from apigee.exceptions import InvalidApisError
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.types import APIGEE_API_CHOICES
from apigee.verbose import common_verbose_options


@click.group(help="Download configuration files from Apigee that can later be restored.")
def backups():
    pass


def validate_resources(apis):
    invalid = [choice for choice in apis if choice not in APIGEE_API_CHOICES]

    if invalid:
        raise InvalidApisError(f"Invalid API choices: {', '.join(invalid)}")

    return set(apis)


def _take_snapshot(
  username,
  password,
  mfa_secret,
  token,
  zonename,
  org,
  profile,
  target_directory,
  prefix,
  environments,
  apis,
  **kwargs,
):
    api_choices = validate_resources(apis)

    config = BackupConfig(
      authentication=generate_authentication(username, password, mfa_secret, token, zonename),
      org_name=org,
      working_directory=target_directory,
      prefix=prefix,
      api_choices=api_choices,
      environments=list(environments),
    )

    asyncio.run(BackupRunner(config).run())


@backups.command(help="Downloads and generates local snapshots of specified Apigee resources.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option(
  "--target-directory",
  type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=False),
  required=True,
)
@click.option(
  "--apis",
  type=click.Choice(APIGEE_API_CHOICES, case_sensitive=False),
  multiple=True,
  default=APIGEE_API_CHOICES,
  show_default=True,
)
@click.option(
  "-e",
  "--environments",
  multiple=True,
  default=["test", "prod"],
  show_default=True,
)
def take_snapshot(*args, **kwargs):
    _take_snapshot(*args, **kwargs)
