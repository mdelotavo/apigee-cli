import json
import sys
from pathlib import Path

from requests.exceptions import HTTPError
from tqdm import tqdm

import apigee.request
from apigee import APIGEE_ADMIN_API_URL, console
from apigee.encryption_utils import (
  ENCRYPTED_HEADER_BEGIN,
  ENCRYPTED_HEADER_END,
  decrypt_with_gpg,
  encrypt_with_gpg,
  has_encrypted_header,
)
from apigee.keyvaluemaps.serializer import KeyvaluemapsSerializer
from apigee.utils import get_progress_kwargs, read_file_content

# --------------------
# paths
# --------------------

CREATE_KVM = "{api}/v1/organizations/{org}/environments/{env}/keyvaluemaps"
KVM = "{api}/v1/organizations/{org}/environments/{env}/keyvaluemaps/{name}"
KVM_ENTRY = "{api}/v1/organizations/{org}/environments/{env}/keyvaluemaps/{name}/entries/{entry}"
KVM_ENTRIES = "{api}/v1/organizations/{org}/environments/{env}/keyvaluemaps/{name}/entries"
LIST_KVMS = "{api}/v1/organizations/{org}/environments/{env}/keyvaluemaps"
LIST_KEYS = "{api}/v1/organizations/{org}/environments/{env}/keyvaluemaps/{name}/keys"


class Keyvaluemaps:

    def __init__(self, auth, org, name):
        self.auth = auth
        self.org = org
        self.name = name

    def _url(self, template, **kwargs):
        return template.format(api=APIGEE_ADMIN_API_URL, org=self.org, name=self.name, **kwargs)

    # --------------------
    # kvm
    # --------------------

    def create_keyvaluemap(self, env, body):
        return apigee.request.post(
          self._url(CREATE_KVM, env=env),
          self.auth,
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
          },
        )

    def delete_keyvaluemap(self, env):
        return apigee.request.delete(self._url(KVM, env=env), self.auth)

    def get_keyvaluemap(self, env):
        return apigee.request.get(self._url(KVM, env=env), self.auth)

    def list_keyvaluemaps(self, env, prefix=None, format="json"):
        resp = apigee.request.get(self._url(LIST_KVMS, env=env), self.auth)
        return KeyvaluemapsSerializer.serialize_details(resp, format, prefix=prefix)

    # --------------------
    # entries
    # --------------------

    def create_entry(self, env, name, value):
        return apigee.request.post(
          self._url(KVM_ENTRIES, env=env),
          self.auth,
          json={
            "name": name,
            "value": value
          },
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
          },
        )

    def update_entry(self, env, name, value):
        return apigee.request.post(
          self._url(KVM_ENTRY, env=env, entry=name),
          self.auth,
          json={
            "name": name,
            "value": value
          },
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
          },
        )

    def delete_entry(self, env, name):
        return apigee.request.delete(self._url(KVM_ENTRY, env=env, entry=name), self.auth)

    def create_or_update_entry(self, env, entry):
        try:
            self.update_entry(env, entry["name"], entry["value"])
        except HTTPError as e:
            if e.response.status_code != 404:
                raise
            self.create_entry(env, entry["name"], entry["value"])

    # --------------------
    # keys
    # --------------------

    def list_keys(self, env, startkey="", count=1000):
        return apigee.request.get(
          self._url(LIST_KEYS, env=env),
          self.auth,
          params={
            "startkey": startkey,
            "count": count
          },
        )

    def get_key(self, env, name):
        return apigee.request.get(self._url(KVM_ENTRY, env=env, entry=name), self.auth)

    def delete_entries(self, env, entries):
        for e in tqdm(entries, **get_progress_kwargs("Deleting")):
            self.delete_entry(env, e["name"])

    # --------------------
    # encryption
    # --------------------

    @staticmethod
    def encrypt(kvm, secret):
        count = 0
        for e in kvm.get("entry", []):
            val = e.get("value")
            if val and not has_encrypted_header(val):
                e["value"] = (f"{ENCRYPTED_HEADER_BEGIN}"
                              f"{encrypt_with_gpg(secret, val)}"
                              f"{ENCRYPTED_HEADER_END}")
                count += 1
        return kvm, count

    @staticmethod
    def decrypt(kvm, secret):
        count = 0
        for e in kvm.get("entry", []):
            val = e.get("value")
            if val and has_encrypted_header(val):
                decrypted = decrypt_with_gpg(secret, val)
                if not decrypted:
                    sys.exit("Incorrect symmetric key.")
                e["value"] = decrypted
                count += 1
        return kvm, count

    @staticmethod
    def diff(local, remote):
        remote_keys = {e["name"] for e in remote["entry"]}
        return [e for e in local["entry"] if e["name"] not in remote_keys]

    # --------------------
    # sync
    # --------------------

    def push(self, env, file, secret=None):
        local = read_file_content(file, type="json")

        if secret:
            console.echo("Decrypting... ", line_ending="", should_flush=True)
            local, n = self.decrypt(local, secret)
            console.echo("Done." if n else "Nothing to decrypt.")
        elif any(has_encrypted_header(e.get("value")) for e in local["entry"]):
            sys.exit("KVM appears encrypted but no secret provided.")

        self.name = local["name"]

        try:
            self.sync(env, local)
        except HTTPError as e:
            if e.response.status_code != 404:
                raise
            console.echo(f"Creating {self.name}")
            console.echo(self.create_keyvaluemap(env, json.dumps(local)).text)

    def sync(self, env, local):
        remote = self.get_keyvaluemap(env).json()

        removed = self.diff(remote, local)
        updated = [e for e in local["entry"] if e not in remote["entry"]]

        if removed:
            self.delete_entries(env, removed)
            console.echo("Removed entries.")

        if updated:
            for e in tqdm(updated, **get_progress_kwargs("Updating")):
                self.create_or_update_entry(env, e)
            console.echo("Updated entries.")

        if not removed and not updated:
            console.echo("All entries up-to-date.")
