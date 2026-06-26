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


def _client(**kwargs):
    return Keyvaluemaps(
      generate_authentication(
        kwargs["username"],
        kwargs["password"],
        kwargs["mfa_secret"],
        kwargs["token"],
        kwargs["zonename"],
      ),
      kwargs["org"],
      kwargs.get("name"),
    )


# --------------------
# kvm
# --------------------


@keyvaluemaps.command(help="Create a key value map.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-b", "--body", required=True)
def create(**kwargs):
    console.echo(_client(**kwargs).create_keyvaluemap(kwargs["environment"], kwargs["body"]).text)


@keyvaluemaps.command(help="Delete a key value map.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def delete(**kwargs):
    console.echo(_client(**kwargs).delete_keyvaluemap(kwargs["environment"]).text)


@keyvaluemaps.command(help="Get a key value map.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
def get(**kwargs):
    console.echo(_client(**kwargs).get_keyvaluemap(kwargs["environment"]).text)


@keyvaluemaps.command(help="List key value maps.")
@common_auth_options
@common_prefix_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
def list(**kwargs):
    console.echo(_client(**kwargs).list_keyvaluemaps(
      kwargs["environment"],
      prefix=kwargs.get("prefix"),
    ))


@keyvaluemaps.command(help="Update a key value map.")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("-b", "--body", required=True)
def update(**kwargs):
    console.echo(_client(**kwargs).create_keyvaluemap(kwargs["environment"], kwargs["body"]).text)


# --------------------
# entries
# --------------------


@keyvaluemaps.command(help="Create a KVM entry.")
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--entry-name", required=True)
@click.option("--entry-value", required=True)
@common_auth_options
@common_silent_options
@common_verbose_options
def create_entry(**kwargs):
    console.echo(_client(**kwargs).create_entry(
      kwargs["environment"],
      kwargs["entry_name"],
      kwargs["entry_value"],
    ).text)


@keyvaluemaps.command(help="Update a KVM entry.")
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--entry-name", required=True)
@click.option("--updated-value", required=True)
@common_auth_options
@common_silent_options
@common_verbose_options
def update_entry(**kwargs):
    console.echo(_client(**kwargs).update_entry(
      kwargs["environment"],
      kwargs["entry_name"],
      kwargs["updated_value"],
    ).text)


@keyvaluemaps.command(help="Delete a KVM entry.")
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--entry-name", required=True)
@common_auth_options
@common_silent_options
@common_verbose_options
def delete_entry(**kwargs):
    console.echo(_client(**kwargs).delete_entry(
      kwargs["environment"],
      kwargs["entry_name"],
    ).text)


@keyvaluemaps.command(help="Get a key value.")
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--entry-name", required=True)
@common_auth_options
@common_silent_options
@common_verbose_options
def get_value(**kwargs):
    console.echo(_client(**kwargs).get_key(
      kwargs["environment"],
      kwargs["entry_name"],
    ).text)


@keyvaluemaps.command(help="List keys in a KVM.")
@click.option("-n", "--name", required=True)
@click.option("-e", "--environment", required=True)
@click.option("--startkey", default="", show_default=True)
@click.option("--count", type=int, default=100, show_default=True)
@common_auth_options
@common_silent_options
@common_verbose_options
def list_keys(**kwargs):
    console.echo(_client(**kwargs).list_keys(
      kwargs["environment"],
      kwargs["startkey"],
      kwargs["count"],
    ).text)


# --------------------
# sync
# --------------------


@keyvaluemaps.command(help="Push KVM (sync entries).")
@common_auth_options
@common_silent_options
@common_verbose_options
@click.option("-e", "--environment", required=True)
@click.option("-f", "--file", type=click.Path(exists=True), required=True)
@click.option("--symmetric-key", default=APIGEE_CLI_SYMMETRIC_KEY)
def push(**kwargs):
    _client(**kwargs).push(
      kwargs["environment"],
      kwargs["file"],
      secret=kwargs.get("symmetric_key"),
    )


# --------------------
# file ops
# --------------------


@keyvaluemaps.command(name="encrypt", help="Encrypt KVM file.")
@common_silent_options
@common_verbose_options
@click.option("-f", "--file", type=click.Path(exists=True), required=True)
@click.option("--symmetric-key", required=True)
def encrypt_file(**kwargs):
    data = read_file_content(kwargs["file"], type="json")

    console.echo("Encrypting... ", line_ending="", should_flush=True)
    data, count = Keyvaluemaps.encrypt(data, kwargs["symmetric_key"])

    if count:
        write_content_to_file(data, kwargs["file"], indentation=2)
        console.echo("Done.")
        return data

    console.echo("Nothing to encrypt.")
    return ""


@keyvaluemaps.command(name="decrypt", help="Decrypt KVM file.")
@common_silent_options
@common_verbose_options
@click.option("-f", "--file", type=click.Path(exists=True), required=True)
@click.option("--symmetric-key", required=True)
def decrypt_file(**kwargs):
    data = read_file_content(kwargs["file"], type="json")

    console.echo("Decrypting... ", line_ending="", should_flush=True)
    data, count = Keyvaluemaps.decrypt(data, kwargs["symmetric_key"])

    if count:
        write_content_to_file(data, kwargs["file"], indentation=2)
        console.echo("Done.")
        return data

    console.echo("Nothing to decrypt.")
    return ""
