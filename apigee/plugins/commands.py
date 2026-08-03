import configparser
import os
import shutil
import stat
import subprocess
import sys
import uuid
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import urlparse

import click
from click_option_group import MutuallyExclusiveOptionGroup, optgroup
from packaging.requirements import Requirement

from apigee import (
  CMD,
  APIGEE_CLI_PLUGIN_INFO_FILE,
  APIGEE_CLI_PLUGIN_INFO_FILE_LEGACY,
  APIGEE_CLI_PLUGINS_CONFIG_FILE,
  APIGEE_CLI_PLUGINS_INIT_FILE,
  PLUGINS_DIR,
  console,
)
from apigee.silent import common_silent_options
from apigee.utils import (
  for_each_file,
  is_dir,
  is_file,
  mkdir,
  read_file,
  touch,
)
from apigee.verbose import common_verbose_options

try:
    from git import Repo

    HAS_GIT = True
    HELP = "Manage plugin repositories."
except ImportError:
    HAS_GIT = False
    HELP = "Manage plugin repositories. Git is required."


def require_git():
    if not HAS_GIT:
        sys.exit(0)


def init():
    mkdir(PLUGINS_DIR)
    touch(APIGEE_CLI_PLUGINS_INIT_FILE)
    touch(APIGEE_CLI_PLUGINS_CONFIG_FILE)


def read_config(section="sources"):
    cfg = configparser.ConfigParser(allow_no_value=True)
    cfg.read(APIGEE_CLI_PLUGINS_CONFIG_FILE)
    return dict(cfg._sections.get(section, {}))


def write_config(data, section="sources"):
    cfg = configparser.ConfigParser(allow_no_value=True)
    cfg[section] = data

    with open(APIGEE_CLI_PLUGINS_CONFIG_FILE, "w") as f:
        cfg.write(f)


def normalize_git_url(url):
    return url.removesuffix(".git").rstrip("/")


def source_key_from_url(url):
    """
    https://github.com/user/my-plugin.git -> my-plugin
    git@github.com:user/my-plugin.git     -> my-plugin
    """

    url = normalize_git_url(url)

    if url.startswith("git@"):
        path = url.split(":", 1)[1]
    else:
        path = urlparse(url).path

    return Path(path).name


def clone():
    init()
    for name, uri in read_config().items():
        dest = Path(PLUGINS_DIR) / name
        if is_dir(dest):
            continue

        console.echo(f"Installing {name}... ", end="", flush=True)
        try:
            Repo.clone_from(uri, dest)
            console.echo("Done")
        except Exception as e:
            console.echo(e)


def pip_command():
    if sys.executable:
        return [sys.executable, "-m", "pip"]

    if shutil.which("pip"):
        return ["pip"]

    if shutil.which("pip3"):
        return ["pip3"]

    return None


def package_installed(package):
    try:
        version(package)
        return True
    except PackageNotFoundError:
        return False


def parse_requires(info):
    requires = info.get("Requires")

    if not requires:
        return []

    if isinstance(requires, str):
        return requires.split()

    if isinstance(requires, (list, tuple, set)):
        return [str(r).strip() for r in requires if str(r).strip()]

    return []


def package_status(requirement):
    req = Requirement(requirement)

    try:
        installed = version(req.name)
    except PackageNotFoundError:
        return req, None, False

    return (
      req,
      installed,
      req.specifier.contains(installed, prereleases=True),
    )


def install_plugin_dependencies(name=None):
    cmd = pip_command()

    if cmd is None:
        console.echo("Unable to locate pip.")
        return

    required = set()

    def add_dependencies(plugin_name):
        info = plugin_info(plugin_name)

        if info:
            required.update(parse_requires(info))

    if name:
        path = Path(PLUGINS_DIR) / name

        if not is_dir(path):
            console.echo(f'Plugin "{name}" not found.')
            sys.exit(1)

        add_dependencies(name)

    else:

        def fn(path):
            if is_dir(path):
                add_dependencies(Path(path).stem)

        for_each_file(
          PLUGINS_DIR,
          fn,
          glob="[!.][!__]*",
        )

    failed = []

    for requirement in sorted(required):
        req, installed, satisfied = package_status(requirement)

        if satisfied:
            console.echo(f"Checked {req.name} ({requirement})... "
                         f"{installed} installed")
            continue

        if installed is None:
            console.echo(
              f"Installing {requirement}... ",
              end="",
              flush=True,
            )
        else:
            console.echo(
              f"Updating {req.name} ({installed} -> {requirement})... ",
              end="",
              flush=True,
            )

        result = subprocess.run(
          cmd + ["install", requirement],
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL,
        )

        if result.returncode == 0:
            console.echo("Done")
        else:
            console.echo("Failed")
            failed.append(requirement)

    if failed:
        console.echo()
        console.echo("The following dependencies could not be installed automatically:")

        for requirement in failed:
            console.echo(f"  {requirement}")

        console.echo()
        console.echo("Try installing them manually:")
        console.echo(f"  {' '.join(cmd)} install {' '.join(failed)}")


def update_repos(name=None):

    def update_repo(path):
        plugin_name = Path(path).stem

        console.echo(f"Updating {plugin_name}... ", end="", flush=True)

        try:
            repo = Repo(path)

            if repo.bare:
                console.echo("Skipped Git pull (bare repository)")
                return

            if not repo.remotes:
                console.echo("Skipped Git pull (Git repository has no remote)")
                return

            repo.remotes["origin"].pull()
            console.echo("Done")

        except Exception:
            console.echo("Skipped Git pull (not a Git repository)")

    if name:
        path = Path(PLUGINS_DIR) / name

        if not is_dir(path):
            console.echo(f'Plugin "{name}" not found.')
            sys.exit(1)

        update_repo(path)
        return

    def fn(path):
        if is_dir(path):
            update_repo(path)

    for_each_file(
      PLUGINS_DIR,
      fn,
      glob="[!.][!__]*",
    )


def _chmod(func, p, _):
    os.chmod(p, stat.S_IRWXU)
    func(p)


def prune_repos():
    sources = read_config()

    def fn(p):
        if not is_dir(p):
            return

        name = Path(p).stem

        if name in sources:
            return

        repo = Path(p) / ".git"

        if not repo.exists():
            console.echo(f"Skipping {name}: local plugin directory without Git metadata.")
            console.echo("Remove it manually if it is no longer required.")
            return

        console.echo(f"Removing {name}... ", end="", flush=True)

        try:
            try:
                shutil.rmtree(p, onexc=_chmod)
            except TypeError:
                shutil.rmtree(p, onerror=_chmod)

            console.echo("Done")
        except Exception as e:
            console.echo(e)

    for_each_file(PLUGINS_DIR, fn, glob="[!.][!__]*")


def plugin_info(name):
    base = Path(PLUGINS_DIR) / name
    f = base / APIGEE_CLI_PLUGIN_INFO_FILE
    if not f.exists():
        f = base / APIGEE_CLI_PLUGIN_INFO_FILE_LEGACY

    if not is_file(f):
        return None

    return read_file(f, type="json")


def print_commit(name):
    repo = Repo(Path(PLUGINS_DIR) / name)
    console.echo(repo.git.log("--pretty=format:%h - %s (%cr) <%an>", "-1"))


@click.group(help=HELP)
def plugins():
    pass


@plugins.command(help="Edit the plugin source configuration.")
@common_silent_options
@common_verbose_options
@click.option("-a/-A", "--apply-changes/--no-apply-changes", default=False)
def configure(silent, verbose, apply_changes):
    require_git()
    init()

    click.edit(filename=APIGEE_CLI_PLUGINS_CONFIG_FILE)

    if apply_changes:
        clone()
        prune_repos()
    else:
        console.echo("\nRun `apigee plugins update` to apply changes.\n")


@plugins.command(help="Add a plugin source.")
@common_silent_options
@common_verbose_options
@click.argument("url")
@click.option(
  "-k",
  "--key",
  help="Plugin source name. Defaults to the repository name.",
)
def add(silent, verbose, url, key):
    init()

    sources = read_config()

    key = key or source_key_from_url(url)

    normalized = normalize_git_url(url)

    for existing_key, existing_url in sources.items():
        if normalize_git_url(existing_url) == normalized:
            console.echo(f'Source "{existing_key}" already uses "{existing_url}".')
            sys.exit(1)

    if key in sources:
        console.echo(f'Source "{key}" already exists.')
        sys.exit(1)

    sources[key] = url
    write_config(sources)

    console.echo(f'Added "{key}" -> {url}')


@plugins.command(help="Remove a plugin source.")
@common_silent_options
@common_verbose_options
@click.argument("source")
def remove(silent, verbose, source):
    init()

    sources = read_config()

    if source in sources:
        del sources[source]
        write_config(sources)

        console.echo(f'Removed "{source}".')
        return

    normalized = normalize_git_url(source)

    for key, url in list(sources.items()):
        if normalize_git_url(url) == normalized:
            del sources[key]
            write_config(sources)

            console.echo(f'Removed "{key}".')
            return

    console.echo(f'Plugin source "{source}" not found.')
    sys.exit(1)


@plugins.command(help="Install, update, and synchronize plugins with the configured sources.")
@common_silent_options
@common_verbose_options
@click.option("-n", "--name")
def update(silent, verbose, name):
    require_git()
    clone()

    console.echo("Updating plugins")
    console.echo("----------------")
    update_repos(name)

    console.echo()
    console.echo("Checking Python package dependencies")
    console.echo("------------------------------------")
    install_plugin_dependencies(name)


@plugins.command(help="Show configured plugins or plugin information.")
@common_silent_options
@common_verbose_options
@click.option("-n", "--name")
@optgroup.group("Filter options", cls=MutuallyExclusiveOptionGroup)
@optgroup.option("--show-commit-only/--no-show-commit-only", default=False)
@optgroup.option("--show-dependencies-only/--no-show-dependencies-only", default=False)
def show(silent, verbose, name, show_commit_only, show_dependencies_only):
    sources = read_config()

    if not name:
        for k, v in sources.items():
            console.echo(f"{k}: {v}")

        plugins = []

        def fn(p):
            if is_dir(p):
                plugins.append(Path(p).stem)

        for_each_file(
          PLUGINS_DIR,
          fn,
          glob="[!.][!__]*",
        )

        unmanaged = set(plugins) - set(sources)

        if unmanaged:
            console.echo()
            console.echo("Note:")
            console.echo("The following local plugins are not configured as sources:")
            for plugin in sorted(unmanaged):
                console.echo(f"  {plugin}")

            console.echo()
            console.echo("These plugins will remain installed locally but will not "
                         "be updated or removed by the plugin manager.")

        return

    info = plugin_info(name)

    if not info:
        console.echo(f'Plugin "{name}" not found.')
        return

    if show_commit_only:
        require_git()
        print_commit(name)
        return

    if show_dependencies_only:
        if info.get("Requires"):
            console.echo(info["Requires"])
        return

    for k, v in info.items():
        console.echo(f"{k}: {v}")


@plugins.command(help="Remove unmanaged plugin repositories.")
@common_silent_options
@common_verbose_options
def prune(silent, verbose):
    require_git()
    prune_repos()


@plugins.command(help="Create a new plugin project.")
@common_silent_options
@common_verbose_options
@click.argument("name")
@click.option(
  "--requires-format",
  type=click.Choice(["array", "string"], case_sensitive=False),
  default="string",
  show_default=True,
  help="Format to use for the Requires field.",
)
def new(silent, verbose, name, requires_format):
    if requires_format == "array":
        info = """{
  "Homepage": "",
  "Requires": [
    "click>=8.1.3",
    "click-aliases>=1.0.1",
    "click-option-group>=0.5.5",
    "GitPython>=3.1.30"
  ],
  "Maintainer": "",
  "Description-en": ""
}
"""
    elif requires_format == "string":
        info = """{
  "Homepage": "",
  "Requires": "click>=8.1.3 click-aliases>=1.0.1 click-option-group>=0.5.5 GitPython>=3.1.30",
  "Maintainer": "",
  "Description-en": ""
}
"""

    init()

    if not name.isidentifier():
        console.echo(f'Invalid plugin name "{name}".')
        sys.exit(1)

    root = Path(PLUGINS_DIR) / name

    if root.exists():
        console.echo(f'Plugin "{name}" already exists.')
        sys.exit(1)

    module = f"plugin_{uuid.uuid4().hex}"

    mkdir(root)

    (root / "__init__.py").write_text(f"""plugins = []

from .{module} import {name}
plugins.append("{name}")

__all__ = plugins
""")

    (root / f"{module}.py").write_text(
      f'''import click


@click.group()
def {name}():
    """Example Click plugin template."""
    pass


@{name}.command()
@click.argument(
    "message",
)
@click.option(
    "--count",
    "-c",
    type=int,
    default=1,
    show_default=True,
    help="Number of times to print the message.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity level.",
)
@click.option(
    "--enabled/--disabled",
    default=True,
    help="Enable or disable the operation.",
)
@click.option(
    "--tag",
    "-t",
    multiple=True,
    help="Specify multiple tags.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Optional output file.",
)
@click.argument(
    "input_file",
    required=False,
    type=click.File("r"),
)
def hello(
    message,
    count,
    output_format,
    verbose,
    enabled,
    tag,
    output,
    input_file,
):
    """Example command showing common Click arguments and options."""

    result = {{
        "message": message,
        "count": count,
        "format": output_format,
        "verbose": verbose,
        "enabled": enabled,
        "tags": tag,
        "output": output,
        "input": input_file.name if input_file else None,
    }}

    if output_format == "json":
        import json
        result = json.dumps(result, indent=2)

    else:
        result = str(result)

    if output:
        with open(output, "w") as f:
            f.write(result)
    else:
        click.echo(result)
'''
    )

    (root / f"{CMD}-cli-info.json").write_text(info)

    touch(root / "README.md")
    touch(root / "LICENSE")

    console.echo(
      f"""\
Created plugin "{name}" at:
  {root}

Generated module:
  {module}.py

Next steps:
  • Add commands to:
      {module}.py

  • To use this plugin locally:
      Copy the plugin directory into another {CMD}
      plugins directory:
        ~/.{CMD}/plugins/

  • To distribute this plugin:
      1. Initialize a Git repository.
      2. Commit and push it to a remote source
         (GitHub, GitLab, or another Git server).
      3. Add the repository URL to your plugin config:
           {CMD} plugins configure

         Example:

           [sources]
           {name} = https://github.com/<user>/{name}.git

         HTTPS and SSH Git URLs are supported.

      4. Install or update plugins:
           {CMD} plugins update
"""
    )
