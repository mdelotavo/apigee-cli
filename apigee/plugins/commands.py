import configparser
import os
import shutil
import stat
import sys
from os import path
from pathlib import Path

import click
from click_option_group import MutuallyExclusiveOptionGroup, optgroup

from apigee import (APIGEE_CLI_PLUGIN_INFO_FILE,
                    APIGEE_CLI_PLUGIN_INFO_FILE_LEGACY,
                    APIGEE_CLI_PLUGINS_CONFIG_FILE,
                    APIGEE_CLI_PLUGINS_DIRECTORY, APIGEE_CLI_PLUGINS_PATH,
                    console)
from apigee.silent import common_silent_options
from apigee.utils import (create_directory, create_empty_file,
                          execute_function_on_directory_files, is_directory,
                          is_regular_file, read_file_content)
from apigee.verbose import common_verbose_options

# ---- Global Variables ----
IS_GIT_INSTALLED = False
PLUGINS_COMMAND_HELP = (
    "Originally meant to help Darumatic clients automate Apigee and API-related "
    "tasks, but available for anyone to use. Refer to "
    "https://github.com/mdelotavo/apigee-cli-plugins to learn how.")

try:
    from git import Repo
    IS_GIT_INSTALLED = True
except ImportError:
    PLUGINS_COMMAND_HELP = (
        "Simple plugins manager for distributing commands. "
        "[Warning: Git must be installed to use plugin commands]")


# ---- Helper Classes ----
class FileUtils:
    """Internal helper class for file/directory operations."""

    @staticmethod
    def chmod_directory(directory, mode):
        """Recursively change permissions of a directory and its contents."""
        for root, dirs, files in os.walk(directory):
            for d in dirs:
                os.chmod(path.join(root, d), mode)
            for f in files:
                os.chmod(path.join(root, f), mode)


class GitUtils:
    """Internal helper class for Git operations."""

    @staticmethod
    def exit_if_not_installed():
        if not IS_GIT_INSTALLED:
            sys.exit(0)


class PluginManager:
    """Internal helper class for Apigee CLI plugin management."""

    @staticmethod
    def initialize_plugins():
        create_directory(APIGEE_CLI_PLUGINS_DIRECTORY)
        create_empty_file(APIGEE_CLI_PLUGINS_PATH)
        create_empty_file(APIGEE_CLI_PLUGINS_CONFIG_FILE)

    @staticmethod
    def load_config(config_file=APIGEE_CLI_PLUGINS_CONFIG_FILE):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        return config

    @staticmethod
    def clone_repositories(section="sources"):
        PluginManager.initialize_plugins()
        config = PluginManager.load_config()
        if not config._sections:
            return
        sources = dict(config._sections[section])
        for name, uri in sources.items():
            dest = Path(APIGEE_CLI_PLUGINS_DIRECTORY) / name
            if is_directory(dest):
                continue
            try:
                console.echo(f"Installing {name}... ",
                             line_ending="",
                             should_flush=True)
                Repo.clone_from(uri, dest)
                console.echo("Done")
            except Exception as e:
                console.echo(e)

    @staticmethod
    def prune_unused_directories(section="sources"):
        PluginManager.initialize_plugins()
        config = PluginManager.load_config()
        if not config._sections:
            return
        sources = dict(config._sections[section])

        def _func(path_):
            if not is_directory(path_):
                return
            name = Path(path_).stem
            if name in sources:
                return
            console.echo(f"Removing {name}... ",
                         line_ending="",
                         should_flush=True)
            plugin_directory = Path(APIGEE_CLI_PLUGINS_DIRECTORY) / name
            try:
                FileUtils.chmod_directory(str(Path(plugin_directory) / ".git"),
                                          stat.S_IRWXU)
                shutil.rmtree(plugin_directory)
                console.echo("Done")
            except Exception as e:
                console.echo(e)

        return execute_function_on_directory_files(
            APIGEE_CLI_PLUGINS_DIRECTORY, _func, glob="[!.][!__]*")

    @staticmethod
    def update_repositories():

        def _func(path_):
            if not is_directory(path_):
                return
            console.echo(f"Updating {Path(path_).stem}... ",
                         line_ending="",
                         should_flush=True)
            repo = Repo(path_)
            if repo.bare:
                return
            try:
                repo.remotes["origin"].pull()
                console.echo("Done")
            except Exception as e:
                console.echo(e)

        return execute_function_on_directory_files(
            APIGEE_CLI_PLUGINS_DIRECTORY, _func, glob="[!.][!__]*")

    @staticmethod
    def list_sources(section="sources"):
        """Return a dictionary of plugin sources from config."""
        config = PluginManager.load_config()
        return dict(config._sections.get(section, {}))

    @staticmethod
    def get_plugin_info(name):
        """Return the parsed plugin info JSON or None if file missing."""
        plugin_directory = Path(APIGEE_CLI_PLUGINS_DIRECTORY) / name
        info_json = plugin_directory / APIGEE_CLI_PLUGIN_INFO_FILE
        info_legacy = plugin_directory / APIGEE_CLI_PLUGIN_INFO_FILE_LEGACY
        info_file = info_json if info_json.exists() else info_legacy
        if not is_regular_file(info_file):
            return None
        return read_file_content(info_file, type="json")

    @staticmethod
    def print_latest_commit(name):
        """Print the latest Git commit of a plugin repository."""
        GitUtils.exit_if_not_installed()
        repo = Repo(Path(APIGEE_CLI_PLUGINS_DIRECTORY) / name)
        console.echo(
            repo.git.log(
                "--pretty=format:%Cred%h%Creset -%C(yellow)%d%Creset %s "
                "%Cgreen(%cr) %C(bold blue)<%an>%Creset", "-1"))

    @staticmethod
    def print_dependencies(plugins_info):
        """Print the 'Requires' field from plugin info, if any."""
        requires = plugins_info.get("Requires")
        if requires:
            console.echo(requires)

    @staticmethod
    def print_full_info(plugins_info):
        """Print all key/value pairs from plugin info."""
        for key, value in plugins_info.items():
            console.echo(f"{key}: {value}")


# ---- CLI Commands ----
@click.group(help=PLUGINS_COMMAND_HELP)
def plugins():
    pass


@plugins.command(help="Edit config file manually.")
@common_silent_options
@common_verbose_options
@click.option(
    "-a/-A",
    "--apply-changes/--no-apply-changes",
    default=False,
    help="Install plugins from new sources after exiting the editor.",
    show_default=True,
)
def configure(silent, verbose, apply_changes):
    GitUtils.exit_if_not_installed()
    PluginManager.initialize_plugins()
    click.edit(filename=APIGEE_CLI_PLUGINS_CONFIG_FILE)
    if apply_changes:
        PluginManager.clone_repositories()
        PluginManager.prune_unused_directories()
    else:
        console.echo("\n  Run `apigee plugins update` to apply any changes, "
                     "or rerun `apigee plugins configure` with `-a` "
                     "to apply changes automatically.\n")


@plugins.command(help="Update or install plugins.")
@common_silent_options
@common_verbose_options
def update(silent, verbose, section="sources"):
    GitUtils.exit_if_not_installed()
    PluginManager.clone_repositories()
    PluginManager.update_repositories()


@plugins.command(help="Show plugins information.")
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", help="Name of the plugins package")
@optgroup.group("Filter options",
                cls=MutuallyExclusiveOptionGroup,
                help="The filter options")
@optgroup.option(
    "--show-commit-only/--no-show-commit-only",
    default=False,
    help="Only print latest Git commit log",
)
@optgroup.option(
    "--show-dependencies-only/--no-show-dependencies-only",
    default=False,
    help="Only print list of required packages",
)
def show(silent,
         verbose,
         name,
         section="sources",
         show_commit_only=False,
         show_dependencies_only=False):
    """Show plugins sources, info, commits, or dependencies based on options."""

    if not name:
        # List all plugin sources
        sources = PluginManager.list_sources(section)
        for plugin_name, uri in sources.items():
            console.echo(f"{plugin_name}: {uri}")
        return

    plugins_info = PluginManager.get_plugin_info(name)
    if not plugins_info:
        return

    if show_commit_only:
        PluginManager.print_latest_commit(name)
    elif show_dependencies_only:
        PluginManager.print_dependencies(plugins_info)
    else:
        PluginManager.print_full_info(plugins_info)


@plugins.command(help="Prune plugins with removed sources.")
@common_silent_options
@common_verbose_options
def prune(silent, verbose, section="sources"):
    GitUtils.exit_if_not_installed()
    PluginManager.prune_unused_directories()
