import configparser
import sys

import click

from apigee import APIGEE_CLI_CREDENTIALS_FILE


def _current_profile():
    for i, arg in enumerate(sys.argv):
        if arg in ("-P", "--profile") and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return "default"


def _prefix_from_config(profile):
    config = configparser.ConfigParser()
    config.read(APIGEE_CLI_CREDENTIALS_FILE)

    if profile in config:
        return config[profile].get("prefix", "")

    return ""


def common_prefix_options(func):
    prefix = _prefix_from_config(_current_profile())

    return click.option(
      "--prefix",
      default=prefix,
      show_default=True,
      help="team/resource prefix filter",
    )(func)
