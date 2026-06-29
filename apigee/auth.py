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
  APIGEE_CLI_ENABLE_SSL_VERIFY,
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


def _form(**kwargs):
    return "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in kwargs.items())


def _oauth_headers():
    return {
      "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
      "Accept": "application/json;charset=utf-8",
      "Authorization": "Basic ZWRnZWNsaTplZGdlY2xpc2VjcmV0",
    }


def _session():
    s = requests.Session()
    s.verify = APIGEE_CLI_ENABLE_SSL_VERIFY
    s.mount("https://", HTTPAdapter())
    return s


# --------------------
# option attachers
# --------------------


def attach_is_token_option(func, profile):
    is_token = get_config_value(profile, "is_token")
    env = os.getenv("APIGEE_IS_TOKEN", "")
    default = is_token if is_token else env
    return click.option("--token/--no-token", default=str(default).lower() in {"1", "true"}, show_default=True)(func)


def attach_mfa_secret_option(func, profile):
    val = get_config_value(profile, "mfa_secret") or os.getenv("APIGEE_MFA_SECRET")
    return click.option("-mfa", "--mfa-secret", default=val)(func)


def attach_org_option(func, profile):
    val = get_config_value(profile, "org") or os.getenv("APIGEE_ORG")
    return click.option("-o", "--org", default=val, required=(not val))(func)


def attach_password_option(func, profile):
    val = get_config_value(profile, "password") or os.getenv("APIGEE_PASSWORD")
    return click.option("-p", "--password", default=val, required=(not val))(func)


def attach_username_option(func, profile):
    val = get_config_value(profile, "username") or os.getenv("APIGEE_USERNAME")
    return click.option("-u", "--username", default=val, required=(not val))(func)


def attach_zonename_option(func, profile):
    val = get_config_value(profile, "zonename") or os.getenv("APIGEE_ZONENAME")
    return click.option("-z", "--zonename", default=val)(func)


def common_auth_options(func):
    profile = "default"
    for i, arg in enumerate(sys.argv):
        if arg in ("-P", "--profile") and i + 1 < len(sys.argv):
            profile = sys.argv[i + 1]

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
    return Struct(username=username, password=password, mfa_secret=mfa_secret, token=token, zonename=zonename)


def generate_authentication_error_message(e):
    msg = f"{type(e).__name__}: {e}\nDouble check credentials."
    return f"{msg}\nWARNING: APIGEE_CLI_IS_MACHINE_USER={APIGEE_CLI_IS_MACHINE_USER}"


# --------------------
# token logic
# --------------------


def get_access_token_for_token(auth, username, password, session):
    url = APIGEE_ZONENAME_OAUTH_URL.format(zonename=auth.zonename) if auth.zonename else APIGEE_OAUTH_URL

    data = _form(
      username=username,
      password=password,
      grant_type="password",
      response_type="token",
    )

    return session.post(url, headers=_oauth_headers(), data=data).json()


def get_access_token_for_mfa(auth, username, password, session):
    try:
        totp = pyotp.TOTP(auth.mfa_secret)
        code = totp.now()
    except binascii.Error as e:
        sys.exit(f"{type(e).__name__}: {e}")

    data = _form(username=username, password=password, grant_type="password")

    resp = session.post(f"{APIGEE_OAUTH_URL}?mfa_token={code}", headers=_oauth_headers(), data=data)

    try:
        r = resp.json()
        r["access_token"]
        return r
    except KeyError:
        return session.post(
          f"{APIGEE_OAUTH_URL}?mfa_token={totp.now()}",
          headers=_oauth_headers(),
          data=data,
        ).json()


def get_access_token_for_sso(auth, session, passcode):
    refresh = validate_refresh_token(auth)
    url = APIGEE_ZONENAME_OAUTH_URL.format(zonename=auth.zonename)

    if not refresh:
        if not passcode:
            passcode = get_sso_temporary_authentication_code(APIGEE_SAML_LOGIN_URL.format(zonename=auth.zonename))

        data = _form(passcode=passcode, grant_type="password", response_type="token")
    else:
        data = _form(grant_type="refresh_token", refresh_token=refresh)

    resp = session.post(url, headers=_oauth_headers(), data=data).json()

    if "access_token" not in resp:
        sys.exit("Temporary Authentication Code or Refresh Token is invalid.")

    if not refresh:
        with open(APIGEE_CLI_REFRESH_TOKEN_FILE, "w") as f:
            f.write(resp["refresh_token"])

    return resp


def get_access_token(auth, username, password, session, passcode):
    if auth.token or APIGEE_CLI_IS_MACHINE_USER:
        return get_access_token_for_token(auth, username, password, session)
    elif auth.mfa_secret:
        return get_access_token_for_mfa(auth, username, password, session)
    elif auth.zonename:
        return get_access_token_for_sso(auth, session, passcode)


def retrieve_access_token(authentication, passcode=None):
    session = _session()
    data = get_access_token(authentication, authentication.username, authentication.password, session, passcode)

    try:
        return data["access_token"]
    except KeyError as e:
        sys.exit(generate_authentication_error_message(e))


# --------------------
# headers
# --------------------


def set_authentication_headers(authentication_object, custom_headers=None):
    if custom_headers is None:
        custom_headers = {}

    if authentication_object.mfa_secret or authentication_object.token or authentication_object.zonename:
        access_token = validate_access_token(authentication_object)
        if not access_token:
            access_token = retrieve_access_token(authentication_object)
            with open(APIGEE_CLI_ACCESS_TOKEN_FILE, "w") as f:
                f.write(access_token)

        custom_headers["Authorization"] = f"Bearer {access_token}"
    else:
        custom_headers["Authorization"] = ("Basic " + base64.b64encode(f"{authentication_object.username}:{authentication_object.password}".encode()).decode())

    return custom_headers


# --------------------
# jwt validation
# --------------------


def validate_jwt_token(authentication_object, file_name, username_field):
    create_directory(APIGEE_CLI_DIRECTORY)

    token = ""
    with contextlib.suppress(IOError, OSError):
        with open(file_name) as f:
            token = f.read().strip()

    if not token:
        return ""

    decoded = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})

    if decoded["exp"] < int(time.time()) or decoded[username_field].lower() != authentication_object.username.lower():
        return ""

    return token


def validate_access_token(authentication_object):
    return validate_jwt_token(authentication_object, APIGEE_CLI_ACCESS_TOKEN_FILE, "email")


def validate_refresh_token(authentication_object):
    return validate_jwt_token(authentication_object, APIGEE_CLI_REFRESH_TOKEN_FILE, "user_name")


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

    messages = [
      "SSO authorization page has automatically been opened in your default browser.",
      "Follow the instructions in the browser to complete this authorization request.",
      f"""\nIf your browser did not automatically open, go to the following URL and sign in:\n\n{url}\n\nthen copy the Temporary Authentication Code.\n"""
    ]

    for msg in messages:
        console.echo(msg)

    return click.prompt("Please enter the Temporary Authentication Code")


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

    if auth_obj.mfa_secret or auth_obj.token or auth_obj.zonename:
        set_authentication_headers(auth_obj)
        console.echo(validate_access_token(auth_obj))
    else:
        console.echo(base64.b64encode(f"{auth_obj.username}:{auth_obj.password}".encode()).decode())


@auth.command()
@common_verbose_options
@common_silent_options
def clear(**_):
    for f in (APIGEE_CLI_ACCESS_TOKEN_FILE, APIGEE_CLI_REFRESH_TOKEN_FILE):
        if os.path.isfile(f):
            os.remove(f)
            console.echo(f"Removed {f}")
        else:
            console.echo(f"{f} not found")
