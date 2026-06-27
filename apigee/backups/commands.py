import click

from apigee.auth import common_auth_options, generate_authentication
from apigee.backups import BackupConfig, Backups
from apigee.exceptions import InvalidApisError
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.types import APIGEE_API_CHOICES
from apigee.verbose import common_verbose_options


@click.group(help="Download configuration files from Apigee that can later be restored.")
def backups():
    pass


# --------------------
# validation
# --------------------


def validate_resources(apis):
    invalid = [a for a in apis if a not in APIGEE_API_CHOICES]

    if invalid:
        raise InvalidApisError(f"Invalid API choices: {', '.join(invalid)}")

    return set(apis)


# --------------------
# execution
# --------------------


def _take_snapshot(**kwargs):
    api_choices = validate_resources(kwargs["apis"])

    config = BackupConfig(
      authentication=generate_authentication(
        kwargs["username"],
        kwargs["password"],
        kwargs["mfa_secret"],
        kwargs["token"],
        kwargs["zonename"],
      ),
      org_name=kwargs["org"],
      working_directory=kwargs["target_directory"],
      prefix=kwargs.get("prefix"),
      api_choices=api_choices,
      environments=list(kwargs["environments"]),
    )

    Backups(config).run()


# --------------------
# command
# --------------------


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
def take_snapshot(**kwargs):
    _take_snapshot(**kwargs)
