import sys
import click

from apigee import APIGEE_CLI_SYMMETRIC_KEY, console
from apigee.auth import common_auth_options, generate_authentication
from apigee.encryption_utils import has_encrypted_header
from apigee.keyvaluemaps.keyvaluemaps import Keyvaluemaps
from apigee.prefix import common_prefix_options
from apigee.silent import common_silent_options
from apigee.utils import read_file_content, write_content_to_file
from apigee.verbose import common_verbose_options


@click.group(help="Manage environment-scoped KeyValueMaps.")
def keyvaluemaps():
    pass


def _client(username, password, mfa_secret, token, zonename, org, name=None):
    return Keyvaluemaps(generate_authentication(username, password, mfa_secret, token, zonename), org, name)


@keyvaluemaps.command(help="Create a key value map.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-b", "--body", required=True)
def create(username, password, mfa_secret, token, zonename, org, profile, name, environment, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).create_kvm(environment, body).text)


@keyvaluemaps.command(help="Delete a key value map.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def delete(username, password, mfa_secret, token, zonename, org, profile, name, environment, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete_kvm(environment).text)


@keyvaluemaps.command(help="Delete a KVM entry.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--entry-name", required=True)
def delete_entry(username, password, mfa_secret, token, zonename, org, profile, name, environment, entry_name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).delete_entry(environment, entry_name).text)


@keyvaluemaps.command(help="Get a key value map.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def get(username, password, mfa_secret, token, zonename, org, profile, name, environment, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get_kvm(environment).text)


@keyvaluemaps.command(help="Get a key value.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--entry-name", required=True)
def get_value(username, password, mfa_secret, token, zonename, org, profile, name, environment, entry_name, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).get_key(environment, entry_name).text)


@keyvaluemaps.command(help="List key value maps.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
def list(username, password, mfa_secret, token, zonename, org, profile, environment, prefix, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org).list_kvms(environment, prefix=prefix))


@keyvaluemaps.command(help="Update a key value map.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-b", "--body", required=True)
def update(username, password, mfa_secret, token, zonename, org, profile, name, environment, body, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).create_kvm(environment, body).text)


@keyvaluemaps.command(help="Create a KVM entry.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--entry-name", required=True)
@click.option("--entry-value", required=True)
def create_entry(username, password, mfa_secret, token, zonename, org, profile, name, environment, entry_name, entry_value, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).create_entry(environment, entry_name, entry_value).text)


@keyvaluemaps.command(help="Update a KVM entry.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--entry-name", required=True)
@click.option("--updated-value", required=True)
def update_entry(username, password, mfa_secret, token, zonename, org, profile, name, environment, entry_name, updated_value, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).update_entry(environment, entry_name, updated_value).text)


@keyvaluemaps.command(help="List keys in a KVM.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--startkey", default="", show_default=True)
@click.option("--count", type=int, default=100, show_default=True)
def list_keys(username, password, mfa_secret, token, zonename, org, profile, name, environment, startkey, count, **_):
    console.echo(_client(username, password, mfa_secret, token, zonename, org, name).list_keys(environment, startkey, count).text)


@keyvaluemaps.command(help="Push KVM (sync entries).")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
@click.option(
  "-f",
  "--file",
  type=click.Path(exists=True, dir_okay=False, file_okay=True),
  required=True,
)
@click.option("--symmetric-key", default=APIGEE_CLI_SYMMETRIC_KEY)
def push(username, password, mfa_secret, token, zonename, org, profile, environment, file, symmetric_key, **_):
    _client(username, password, mfa_secret, token, zonename, org).push(environment, file, secret=symmetric_key)


@keyvaluemaps.command(name="encrypt", help="Encrypt KVM file.")
@common_silent_options
@common_verbose_options
@click.option(
  "-f",
  "--file",
  type=click.Path(exists=True, dir_okay=False, file_okay=True),
  required=True,
)
@click.option("--symmetric-key", required=True)
def encrypt_file(symmetric_key, file, **_):
    data = read_file_content(file, type="json")
    console.echo("Encrypting... ", line_ending="", should_flush=True)

    data, count = Keyvaluemaps.encrypt(data, symmetric_key)

    if count:
        write_content_to_file(data, file, indentation=2)
        console.echo("Done.")
        return data

    console.echo("Nothing to encrypt.")
    return ""


@keyvaluemaps.command(name="decrypt", help="Decrypt KVM file.")
@common_silent_options
@common_verbose_options
@click.option(
  "-f",
  "--file",
  type=click.Path(exists=True, dir_okay=False, file_okay=True),
  required=True,
)
@click.option("--symmetric-key", required=True)
def decrypt_file(symmetric_key, file, **_):
    data = read_file_content(file, type="json")
    console.echo("Decrypting... ", line_ending="", should_flush=True)

    data, count = Keyvaluemaps.decrypt(data, symmetric_key)

    if count:
        write_content_to_file(data, file, indentation=2)
        console.echo("Done.")
        return data

    console.echo("Nothing to decrypt.")
    return ""
