import base64
import binascii
import configparser
import contextlib
import os
import sys
import time
import urllib.parse
import webbrowser

import click
import jwt
import pyotp
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError

from apigee import (
  APIGEE_CLI_ACCESS_TOKEN_FILE,
  APIGEE_CLI_CREDENTIALS_FILE,
  APIGEE_CLI_DIRECTORY,
  APIGEE_CLI_IS_MACHINE_USER,
  APIGEE_CLI_REFRESH_TOKEN_FILE,
  APIGEE_OAUTH_URL,
  APIGEE_SAML_LOGIN_URL,
  APIGEE_ZONENAME_OAUTH_URL,
  console,
)
from apigee.cls import AliasedGroup
from apigee.silent import common_silent_options
from apigee.types import Struct
from apigee.utils import create_directory
from apigee.verbose import common_verbose_options

# --------------------
# helpers
# --------------------


def _env_or_config(profile, key, env):
    val = get_config_value(profile, key)
    return val or os.getenv(env)


def _bool(val):
    return str(val).lower() in {"true", "1"}


def _attach_option(func, option, value, env_value=None, required=False, **kwargs):
    default = value or env_value
    return click.option(
      *option,
      default=default if default else None,
      required=(not default and required),
      show_default=bool(default),
      **kwargs,
    )(func)


# --------------------
# click option attachers
# --------------------


def attach_username_option(func, profile):
    return _attach_option(func, ("-u", "--username"), _env_or_config(profile, "username", "APIGEE_USERNAME"))


def attach_password_option(func, profile):
    return _attach_option(func, ("-p", "--password"), _env_or_config(profile, "password", "APIGEE_PASSWORD"))


def attach_org_option(func, profile):
    return _attach_option(func, ("-o", "--org"), _env_or_config(profile, "org", "APIGEE_ORG"), required=True)


def attach_mfa_secret_option(func, profile):
    return _attach_option(func, ("-mfa", "--mfa-secret"), _env_or_config(profile, "mfa_secret", "APIGEE_MFA_SECRET"))


def attach_zonename_option(func, profile):
    return _attach_option(func, ("-z", "--zonename"), _env_or_config(profile, "zonename", "APIGEE_ZONENAME"))


def attach_is_token_option(func, profile):
    val = _env_or_config(profile, "is_token", "APIGEE_IS_TOKEN")
    return click.option(
      "--token/--no-token",
      default=_bool(val),
      show_default=True,
      help="use OAuth without MFA",
    )(func)


def common_auth_options(func):
    profile = next(
      (sys.argv[i + 1] for i, a in enumerate(sys.argv) if a in ("-P", "--profile") and i + 1 < len(sys.argv)),
      "default",
    )

    for attach in (
      attach_username_option,
      attach_password_option,
      attach_mfa_secret_option,
      attach_is_token_option,
      attach_zonename_option,
      attach_org_option,
    ):
        func = attach(func, profile)

    return click.option("-P", "--profile", default=profile, show_default=True)(func)


# --------------------
# auth struct
# --------------------


def generate_authentication(username=None, password=None, mfa_secret=None, token=None, zonename=None):
    return Struct(
      username=username,
      password=password,
      mfa_secret=mfa_secret,
      token=token,
      zonename=zonename,
    )


# --------------------
# token logic
# --------------------


def _session():
    s = requests.Session()
    s.mount("https://", HTTPAdapter())
    return s


def _post(session, url, headers, data):
    resp = session.post(url, headers=headers, data=data)
    resp.raise_for_status()
    return resp.json()


def _form(**kwargs):
    return "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in kwargs.items())


def _oauth_headers():
    return {
      "Content-Type": "application/x-www-form-urlencoded",
      "Accept": "application/json",
      "Authorization": "Basic ZWRnZWNsaTplZGdlY2xpc2VjcmV0",
    }


def get_access_token(auth, session, passcode=None):
    username = auth.username
    password = auth.password

    if auth.token or APIGEE_CLI_IS_MACHINE_USER:
        url = APIGEE_ZONENAME_OAUTH_URL.format(zonename=auth.zonename) if auth.zonename else APIGEE_OAUTH_URL
        return _post(session, url, _oauth_headers(), _form(username=username, password=password, grant_type="password"))

    if auth.mfa_secret:
        try:
            totp = pyotp.TOTP(auth.mfa_secret)
            code = totp.now()
        except binascii.Error:
            sys.exit("Invalid MFA key")

        return _post(session, APIGEE_OAUTH_URL + f"?mfa_token={code}", _oauth_headers(), _form(username=username, password=password, grant_type="password"))

    if auth.zonename:
        return _get_sso_token(auth, session, passcode)


def _get_sso_token(auth, session, passcode):
    url = APIGEE_ZONENAME_OAUTH_URL.format(zonename=auth.zonename)
    refresh = validate_refresh_token(auth)

    if not refresh:
        passcode = passcode or get_sso_temporary_authentication_code(APIGEE_SAML_LOGIN_URL.format(zonename=auth.zonename))
        data = _form(passcode=passcode, grant_type="password")
    else:
        data = _form(grant_type="refresh_token", refresh_token=refresh)

    resp = _post(session, url, _oauth_headers(), data)

    if "refresh_token" in resp:
        with open(APIGEE_CLI_REFRESH_TOKEN_FILE, "w") as f:
            f.write(resp["refresh_token"])

    return resp


def retrieve_access_token(auth, passcode=None):
    try:
        return get_access_token(auth, _session(), passcode)["access_token"]
    except KeyError as e:
        sys.exit(f"Auth error: {e}")


# --------------------
# headers
# --------------------


def set_authentication_headers(auth_obj, headers=None):
    headers = headers or {}

    if auth_obj.mfa_secret or auth_obj.token or auth_obj.zonename:
        token = validate_access_token(auth_obj) or retrieve_access_token(auth_obj)
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{auth_obj.username}:{auth_obj.password}".encode()).decode()

    return headers


# --------------------
# jwt validation
# --------------------


def validate_jwt_token(auth_obj, file_name, field):
    create_directory(APIGEE_CLI_DIRECTORY)

    token = ""
    with contextlib.suppress(IOError):
        with open(file_name) as f:
            token = f.read().strip()

    if not token:
        return ""

    decoded = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
    if decoded["exp"] < int(time.time()) or decoded[field].lower() != auth_obj.username.lower():
        return ""

    return token


def validate_access_token(auth):
    return validate_jwt_token(auth, APIGEE_CLI_ACCESS_TOKEN_FILE, "email")


def validate_refresh_token(auth):
    return validate_jwt_token(auth, APIGEE_CLI_REFRESH_TOKEN_FILE, "user_name")


# --------------------
# config
# --------------------


def get_config_value(section, key):
    cfg = configparser.ConfigParser()
    cfg.read(APIGEE_CLI_CREDENTIALS_FILE)
    return cfg.get(section, key, fallback=None)


# --------------------
# sso
# --------------------


def get_sso_temporary_authentication_code(url):
    webbrowser.open(url)
    console.echo("Complete SSO login in browser.")
    return click.prompt("Enter Temporary Authentication Code")


# --------------------
# CLI
# --------------------


@click.command(cls=AliasedGroup)
def auth():
    pass


@auth.command(name="get-access-token")
@common_auth_options
@common_verbose_options
@common_silent_options
@click.option("--passcode")
def get_access_token_command(username, password, mfa_secret, token, zonename, org, profile, passcode, **_):
    console.echo(retrieve_access_token(generate_authentication(username, password, mfa_secret, token, zonename), passcode))


@auth.command()
@common_auth_options
@common_verbose_options
@common_silent_options
def view_access_token(username, password, mfa_secret, token, zonename, org, profile, **_):
    auth_obj = generate_authentication(username, password, mfa_secret, token, zonename)
    console.echo(validate_access_token(auth_obj) or "No valid token")


@auth.command()
def clear():
    for f in (APIGEE_CLI_ACCESS_TOKEN_FILE, APIGEE_CLI_REFRESH_TOKEN_FILE):
        if os.path.isfile(f):
            os.remove(f)
            console.echo(f"Removed {f}")
