import builtins
from os import getenv
from pathlib import Path

from apigee import utils_init

APP = "apigeecli"
CMD = "apigee"

__version__ = "0.54.0"

description = "(DEPRECATED) User-friendly wrapper for the Apigee Edge admin APIs."
long_description = (
  "apigeecli is an unofficial Python command-line tool built to simplify "
  "and automate Apigee Edge API usage, with support for SSO, MFA, and basic authentication."
)

# --------------------
# Paths
# --------------------

HOME = Path.home()
APIGEE_CLI_DIRECTORY = utils_init.join_path_components(HOME, ".apigee")
PLUGINS_DIR = utils_init.join_path_components(APIGEE_CLI_DIRECTORY, "plugins")

APIGEE_CLI_ACCESS_TOKEN_FILE = utils_init.join_path_components(APIGEE_CLI_DIRECTORY, "access_token")
APIGEE_CLI_REFRESH_TOKEN_FILE = utils_init.join_path_components(APIGEE_CLI_DIRECTORY, "refresh_token")
APIGEE_CLI_CREDENTIALS_FILE = utils_init.join_path_components(APIGEE_CLI_DIRECTORY, "credentials")
APIGEE_CLI_EXCEPTIONS_LOG_FILE = utils_init.join_path_components(APIGEE_CLI_DIRECTORY, "exceptions.log")

APIGEE_CLI_PLUGINS_CONFIG_FILE = utils_init.join_path_components(PLUGINS_DIR, "config")
APIGEE_CLI_PLUGINS_PATH = utils_init.join_path_components(PLUGINS_DIR, "__init__.py")

# --------------------
# API endpoints
# --------------------

APIGEE_ADMIN_API_URL = "https://api.enterprise.apigee.com"
APIGEE_OAUTH_URL = "https://login.apigee.com/oauth/token"
APIGEE_SAML_LOGIN_URL = "https://{zonename}.login.apigee.com/passcode"
APIGEE_ZONENAME_OAUTH_URL = "https://{zonename}.login.apigee.com/oauth/token"

# --------------------
# Plugin metadata
# --------------------

APIGEE_CLI_PLUGIN_INFO_FILE = "apigee-cli-info.json"
APIGEE_CLI_PLUGIN_INFO_FILE_LEGACY = "apigee-cli.info"

# --------------------
# Environment variables
# --------------------

APIGEE_ORG = getenv("APIGEE_ORG")
APIGEE_USERNAME = getenv("APIGEE_USERNAME")
APIGEE_PASSWORD = getenv("APIGEE_PASSWORD")
APIGEE_MFA_SECRET = getenv("APIGEE_MFA_SECRET")
APIGEE_ZONENAME = getenv("APIGEE_ZONENAME")

APIGEE_IS_TOKEN = getenv("APIGEE_IS_TOKEN")
APIGEE_CLI_PREFIX = getenv("APIGEE_CLI_PREFIX")
APIGEE_CLI_SYMMETRIC_KEY = getenv("APIGEE_CLI_SYMMETRIC_KEY")

APIGEE_CLI_IS_MACHINE_USER = utils_init.is_truthy_envvar(getenv("APIGEE_CLI_IS_MACHINE_USER"))

# --------------------
# Runtime flags
# --------------------

APIGEE_CLI_TOGGLE_SILENT = False
APIGEE_CLI_TOGGLE_VERBOSE = 0

# expose globally
builtins.APIGEE_CLI_TOGGLE_SILENT = APIGEE_CLI_TOGGLE_SILENT
builtins.APIGEE_CLI_TOGGLE_VERBOSE = APIGEE_CLI_TOGGLE_VERBOSE
