import json
import sys

import requests
from requests.exceptions import HTTPError
from tqdm import tqdm

from apigee import APIGEE_ADMIN_API_URL, auth, console
from apigee.encryption_utils import (
  ENCRYPTED_HEADER_BEGIN,
  ENCRYPTED_HEADER_END,
  decrypt_with_gpg,
  encrypt_with_gpg,
  has_encrypted_header,
)
from apigee.keyvaluemaps.serializer import KeyvaluemapsSerializer
from apigee.utils import read_file_content

CREATE_KEYVALUEMAP_PATH = "/v1/organizations/{org}/environments/{env}/keyvaluemaps"
KVM_PATH = "/v1/organizations/{org}/environments/{env}/keyvaluemaps/{name}"
KVM_ENTRY_PATH = "/v1/organizations/{org}/environments/{env}/keyvaluemaps/{name}/entries/{entry}"
KVM_ENTRIES_PATH = "/v1/organizations/{org}/environments/{env}/keyvaluemaps/{name}/entries"
LIST_KVMS_PATH = "/v1/organizations/{org}/environments/{env}/keyvaluemaps"
LIST_KEYS_PATH = "/v1/organizations/{org}/environments/{env}/keyvaluemaps/{name}/keys"


def _progress(desc):
    return {"desc": desc, "unit": "entries", "leave": False, "bar_format": "{l_bar}{bar:32}{r_bar}{bar:-10b}"}


class Keyvaluemaps:

    def __init__(self, auth_config, org, name):
        self.auth = auth_config
        self.org = org
        self.name = name

    def _headers(self, extra=None):
        return auth.set_authentication_headers(
          self.auth,
          custom_headers={
            "Accept": "application/json",
            **(extra or {})
          },
        )

    def _request(self, method, path, **kwargs):
        url = f"{APIGEE_ADMIN_API_URL}{path}"
        resp = requests.request(method, url, headers=self._headers(kwargs.pop("headers", None)), **kwargs)
        resp.raise_for_status()
        return resp

    def create_kvm(self, env, body):
        return self._request(
          "post",
          CREATE_KEYVALUEMAP_PATH.format(org=self.org, env=env),
          headers={"Content-Type": "application/json"},
          json=json.loads(body),
        )

    def delete_kvm(self, env):
        return self._request("delete", KVM_PATH.format(org=self.org, env=env, name=self.name))

    def get_kvm(self, env):
        return self._request("get", KVM_PATH.format(org=self.org, env=env, name=self.name))

    def list_kvms(self, env, prefix=None, format="json"):
        resp = self._request("get", LIST_KVMS_PATH.format(org=self.org, env=env))
        return KeyvaluemapsSerializer().serialize_details(resp, format, prefix=prefix)

    def create_entry(self, env, name, value):
        return self._request(
          "post",
          KVM_ENTRIES_PATH.format(org=self.org, env=env, name=self.name),
          headers={"Content-Type": "application/json"},
          json={
            "name": name,
            "value": value
          },
        )

    def update_entry(self, env, name, value):
        return self._request(
          "post",
          KVM_ENTRY_PATH.format(org=self.org, env=env, name=self.name, entry=name),
          headers={"Content-Type": "application/json"},
          json={
            "name": name,
            "value": value
          },
        )

    def delete_entry(self, env, name):
        return self._request("delete", KVM_ENTRY_PATH.format(org=self.org, env=env, name=self.name, entry=name))

    def create_or_update_entry(self, env, entry):
        try:
            self.update_entry(env, entry["name"], entry["value"])
        except HTTPError as e:
            if e.response.status_code != 404:
                raise
            self.create_entry(env, entry["name"], entry["value"])

    def list_keys(self, env, startkey="", count=1000):
        return self._request(
          "get",
          LIST_KEYS_PATH.format(org=self.org, env=env, name=self.name),
          params={
            "startkey": startkey,
            "count": count
          },
        )

    def get_key(self, env, name):
        return self._request("get", KVM_ENTRY_PATH.format(org=self.org, env=env, name=self.name, entry=name))

    def delete_entries(self, env, entries):
        for e in tqdm(entries, **_progress("Deleting")):
            self.delete_entry(env, e["name"])

    @staticmethod
    def encrypt(kvm, secret):
        count = 0
        for e in kvm.get("entry", []):
            val = e.get("value")
            if val and not has_encrypted_header(val):
                e["value"] = f"{ENCRYPTED_HEADER_BEGIN}{encrypt_with_gpg(secret, val)}{ENCRYPTED_HEADER_END}"
                count += 1
        return kvm, count

    @staticmethod
    def decrypt(kvm, secret):
        count = 0
        for e in kvm.get("entry", []):
            val = e.get("value")
            if val and has_encrypted_header(val):
                decrypted = decrypt_with_gpg(secret, val)
                if decrypted == "":
                    sys.exit("Incorrect symmetric key.")
                e["value"] = decrypted
                count += 1
        return kvm, count

    @staticmethod
    def diff(local, remote):
        remote_names = {e["name"] for e in remote["entry"]}
        return [e for e in local["entry"] if e["name"] not in remote_names]

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
            console.echo(self.create_kvm(env, json.dumps(local)).text)

    def sync(self, env, local):
        remote = self.get_kvm(env).json()

        removed = self.diff(remote, local)
        updated = [e for e in local["entry"] if e not in remote["entry"]]

        if removed:
            self.delete_entries(env, removed)
            console.echo("Removed entries.")

        if updated:
            for e in tqdm(updated, **_progress("Updating")):
                self.create_or_update_entry(env, e)
            console.echo("Updated entries.")

        if not removed and not updated:
            console.echo("All entries up-to-date.")
