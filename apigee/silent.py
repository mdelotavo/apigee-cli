import builtins
import click


def _set_silent(ctx, param, value):
    builtins.APIGEE_CLI_TOGGLE_SILENT = value
    return value


def common_silent_options(func):
    return click.option(
      "--silent",
      is_flag=True,
      default=False,
      show_default=True,
      help="toggle silent output",
      callback=_set_silent,
    )(func)
