import configparser
import sys

import click

from apigee import APIGEE_CLI_CREDENTIALS_FILE, APIGEE_CLI_DIRECTORY
from apigee.utils import create_directory
from apigee.utils_init import is_truthy_envvar

KEYS = ("username", "password", "mfa_secret", "is_token", "zonename", "org", "prefix")


class HiddenSecret:

    def __init__(self, value=""):
        self.value = value

    def __str__(self):
        return "*" * 16 if self.value else ""


def _get_profile_name():
    args = sys.argv
    for i, arg in enumerate(args):
        if arg in ("-P", "--profile") and i + 1 < len(args):
            return args[i + 1]
    return "default"


def _load_profile(name):
    cfg = configparser.ConfigParser()
    cfg.read(APIGEE_CLI_CREDENTIALS_FILE)

    data = dict(cfg._sections.get(name, {}))
    return {k: data.get(k, "") for k in KEYS}, cfg


profile_name = _get_profile_name()
profile_data, config = _load_profile(profile_name)


@click.command(help="Configure Apigee Edge credentials.")
@click.option(
  "-u",
  "--username",
  prompt="Apigee username (email)",
  default=profile_data["username"],
  show_default=True,
)
@click.option(
  "-p",
  "--password",
  prompt="Apigee password",
  default=lambda: HiddenSecret(profile_data["password"]),
  hide_input=True,
  show_default="hidden" if profile_data["password"] else "None",
)
@click.option(
  "-mfa",
  "--mfa-secret",
  prompt="Apigee MFA key (optional)",
  default=lambda: HiddenSecret(profile_data["mfa_secret"]),
  hide_input=True,
  show_default="hidden" if profile_data["mfa_secret"] else "None",
)
@click.option(
  "-z",
  "--zonename",
  prompt="Identity zone name",
  default=profile_data["zonename"],
  show_default=True,
)
@click.option(
  "--token/--no-token",
  default=is_truthy_envvar(profile_data["is_token"]),
  prompt="Use OAuth, no MFA (optional)?",
  show_default=True,
)
@click.option(
  "-o",
  "--org",
  prompt="Default Apigee organization",
  default=profile_data["org"],
  show_default=True,
)
@click.option(
  "--prefix",
  prompt="Default team/resource prefix",
  default=profile_data["prefix"],
  show_default=True,
)
@click.option(
  "-P",
  "--profile",
  default="default",
  show_default=True,
)
def configure(username, password, mfa_secret, token, zonename, org, prefix, profile):

    password = password.value if isinstance(password, HiddenSecret) else password
    mfa_secret = mfa_secret.value if isinstance(mfa_secret, HiddenSecret) else mfa_secret

    data = {
      "username": username,
      "password": password,
      "mfa_secret": mfa_secret,
      "is_token": token,
      "zonename": zonename,
      "org": org,
      "prefix": prefix,
    }

    config[profile] = {k: v for k, v in data.items() if v}

    create_directory(APIGEE_CLI_DIRECTORY)

    with open(APIGEE_CLI_CREDENTIALS_FILE, "w") as f:
        config.write(f)
