#!/usr/bin/env python
# __main__.py

import click

from apigee import (
  APIGEE_CLI_EXCEPTIONS_LOG_FILE,
  APIGEE_CLI_PLUGINS_DIRECTORY,
  CMD,
)
from apigee import __version__ as version

# commands
from apigee.apiproducts.commands import apiproducts
from apigee.apis.commands import apis
from apigee.apps.commands import apps
from apigee.auth import auth
from apigee.backups.commands import backups
from apigee.caches.commands import caches
from apigee.configure.commands import configure
from apigee.deployments.commands import deployments
from apigee.developers.commands import developers
from apigee.keystores.commands import keystores
from apigee.keyvaluemaps.commands import keyvaluemaps
from apigee.maskconfigs.commands import maskconfigs
from apigee.permissions.commands import permissions
from apigee.plugins.commands import plugins
from apigee.references.commands import references
from apigee.sharedflows.commands import sharedflows
from apigee.targetservers.commands import targetservers
from apigee.userroles.commands import userroles
from apigee.virtualhosts.commands import virtualhosts

from apigee.cls import AliasedGroup
from apigee.exceptions import configure_global_logger, wrap_with_exception_handling
from apigee.utils import execute_function_on_directory_files, import_plugins_from_directory

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS, cls=AliasedGroup)
@click.version_option(version, "-V", "--version")
@click.pass_context
def cli(ctx):
    """Apigee CLI (unofficial)."""
    ctx.ensure_object(dict)


# --------------------
# command registry
# --------------------

DEFAULT_COMMANDS = [
  backups,
  configure,
  deployments,
  caches,
  keyvaluemaps,
  targetservers,
  apis,
  apiproducts,
  apps,
  developers,
  auth,
  maskconfigs,
  userroles,
  permissions,
  sharedflows,
  keystores,
  references,
  virtualhosts,
  plugins,
]


def _load_plugins(commands):
    execute_function_on_directory_files(
      APIGEE_CLI_PLUGINS_DIRECTORY,
      import_plugins_from_directory,
      args=(commands, ),
      glob="[!.][!__]*/__init__.py",
    )


def _register_commands(commands):
    for cmd in commands:
        cli.add_command(cmd)


# --------------------
# entrypoint
# --------------------


@wrap_with_exception_handling
def main():
    configure_global_logger(APIGEE_CLI_EXCEPTIONS_LOG_FILE)

    commands = list(DEFAULT_COMMANDS)

    _load_plugins(commands)
    _register_commands(commands)

    cli(prog_name=CMD, obj={})


if __name__ == "__main__":
    main()
