import builtins
import http.client as http_client
import logging

import click


def _set_verbose(ctx, param, value):
    builtins.APIGEE_CLI_TOGGLE_VERBOSE = value

    http_client.HTTPConnection.debuglevel = value

    if value > 0:
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)

    return value


def common_verbose_options(func):
    return click.option(
      "-v",
      "--verbose",
      count=True,
      default=0,
      show_default=True,
      help="increase verbosity (use multiple times for more detail)",
      callback=_set_verbose,
    )(func)
