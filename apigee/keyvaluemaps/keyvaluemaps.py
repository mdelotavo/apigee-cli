import json
import sys
from typing import Tuple

import requests
from requests.exceptions import HTTPError
from tqdm import tqdm

from apigee import APIGEE_ADMIN_API_URL, auth, console
from apigee.encryption_utils import (ENCRYPTED_HEADER_BEGIN,
                                     ENCRYPTED_HEADER_END,
                                     decrypt_message_with_gpg,
                                     encrypt_message_with_gpg,
                                     has_encrypted_header)
from apigee.keyvaluemaps.serializer import KeyvaluemapsSerializer
from apigee.utils import get_tqdm_kwargs, read_file_content

# API path templates
CREATE_KEYVALUEMAP_IN_AN_ENVIRONMENT_PATH = "{api_url}/v1/organizations/{org}/environments/{environment}/keyvaluemaps"
DELETE_KEYVALUEMAP_FROM_AN_ENVIRONMENT_PATH = "{api_url}/v1/organizations/{org}/environments/{environment}/keyvaluemaps/{name}"
DELETE_KEYVALUEMAP_ENTRY_IN_AN_ENVIRONMENT_PATH = "{api_url}/v1/organizations/{org}/environments/{environment}/keyvaluemaps/{name}/entries/{entry_name}"
GET_KEYVALUEMAP_IN_AN_ENVIRONMENT_PATH = "{api_url}/v1/organizations/{org}/environments/{environment}/keyvaluemaps/{name}"
GET_A_KEYS_VALUE_IN_AN_ENVIRONMENT_SCOPED_KEYVALUEMAP_PATH = "{api_url}/v1/organizations/{org}/environments/{environment}/keyvaluemaps/{name}/entries/{entry_name}"
LIST_KEYVALUEMAPS_IN_AN_ENVIRONMENT_PATH = "{api_url}/v1/organizations/{org}/environments/{environment}/keyvaluemaps"
UPDATE_KEYVALUEMAP_IN_AN_ENVIRONMENT_PATH = "{api_url}/v1/organizations/{org}/environments/{environment}/keyvaluemaps/{name}"
CREATE_AN_ENTRY_IN_AN_ENVIRONMENT_SCOPED_KVM_PATH = "{api_url}/v1/organizations/{org}/environments/{environment}/keyvaluemaps/{name}/entries"
UPDATE_AN_ENTRY_IN_AN_ENVIRONMENT_SCOPED_KVM_PATH = "{api_url}/v1/organizations/{org}/environments/{environment}/keyvaluemaps/{name}/entries/{entry_name}"
LIST_KEYS_IN_AN_ENVIRONMENT_SCOPED_KEYVALUEMAP_PATH = "{api_url}/v1/organizations/{org}/environments/{environment}/keyvaluemaps/{name}/keys?startkey={startkey}&count={count}"


class _RequestHelper:
    """Internal helper for HTTP requests with consistent headers."""

    @staticmethod
    def post(auth_obj, uri, json_body=None):
        resp = requests.post(
            uri,
            headers=auth.set_authentication_headers(auth_obj,
                                                    custom_headers={
                                                        "Accept":
                                                        "application/json",
                                                        "Content-Type":
                                                        "application/json"
                                                    }),
            json=json_body,
        )
        resp.raise_for_status()
        return resp

    @staticmethod
    def get(auth_obj, uri):
        resp = requests.get(
            uri,
            headers=auth.set_authentication_headers(
                auth_obj, custom_headers={"Accept": "application/json"}),
        )
        resp.raise_for_status()
        return resp

    @staticmethod
    def delete(auth_obj, uri):
        resp = requests.delete(
            uri,
            headers=auth.set_authentication_headers(
                auth_obj, custom_headers={"Accept": "application/json"}),
        )
        resp.raise_for_status()
        return resp


class _EncryptionHelper:
    """Internal helper for encrypting and decrypting KVM entries."""

    @staticmethod
    def encrypt_entry(kvm_dict, entry_index, secret) -> int:
        plaintext = kvm_dict["entry"][entry_index]["value"]
        if has_encrypted_header(plaintext):
            return 0
        encrypted_value = f"{ENCRYPTED_HEADER_BEGIN}{encrypt_message_with_gpg(secret, plaintext)}{ENCRYPTED_HEADER_END}"
        kvm_dict["entry"][entry_index]["value"] = encrypted_value
        return 1

    @staticmethod
    def decrypt_entry(kvm_dict, entry_index, secret) -> int:
        ciphertext = kvm_dict["entry"][entry_index]["value"]
        if not has_encrypted_header(ciphertext):
            return 0
        decrypted_value = decrypt_message_with_gpg(secret, ciphertext)
        if decrypted_value == "":
            sys.exit("Incorrect symmetric key.")
        kvm_dict["entry"][entry_index]["value"] = decrypted_value
        return 1


class _SyncHelper:
    """Internal helper for comparing and synchronizing KVM entries."""

    @staticmethod
    def find_deleted_keys(local_map, remote_map):
        return [
            entry for entry in remote_map.get("entry", []) if entry["name"]
            not in {e["name"]
                    for e in local_map.get("entry", [])}
        ]

    @staticmethod
    def entries_to_update(local_map, remote_map):
        return {
            "entry": [
                entry for entry in local_map.get("entry", [])
                if entry not in remote_map.get("entry", [])
            ]
        }


class Keyvaluemaps:
    """Keyvaluemaps manager with full backward compatibility."""

    def __init__(self, auth, org_name, map_name):
        self.auth = auth
        self.org_name = org_name
        self.map_name = map_name

    # ---- Entry CRUD ----
    def create_an_entry_in_an_environment_scoped_kvm(self, environment,
                                                     entry_name, entry_value):
        uri = CREATE_AN_ENTRY_IN_AN_ENVIRONMENT_SCOPED_KVM_PATH.format(
            api_url=APIGEE_ADMIN_API_URL,
            org=self.org_name,
            environment=environment,
            name=self.map_name)
        return _RequestHelper.post(self.auth,
                                   uri,
                                   json_body={
                                       "name": entry_name,
                                       "value": entry_value
                                   })

    def update_an_entry_in_an_environment_scoped_kvm(self, environment,
                                                     entry_name,
                                                     updated_value):
        uri = UPDATE_AN_ENTRY_IN_AN_ENVIRONMENT_SCOPED_KVM_PATH.format(
            api_url=APIGEE_ADMIN_API_URL,
            org=self.org_name,
            environment=environment,
            name=self.map_name,
            entry_name=entry_name,
        )
        return _RequestHelper.post(self.auth,
                                   uri,
                                   json_body={
                                       "name": entry_name,
                                       "value": updated_value
                                   })

    def create_or_update_entry(self, environment, entry):
        try:
            self.update_an_entry_in_an_environment_scoped_kvm(
                environment, entry["name"], entry["value"])
        except HTTPError as e:
            if e.response.status_code != 404:
                raise
            self.create_an_entry_in_an_environment_scoped_kvm(
                environment, entry["name"], entry["value"])

    def delete_keyvaluemap_entry_in_an_environment(self, environment,
                                                   entry_name):
        uri = DELETE_KEYVALUEMAP_ENTRY_IN_AN_ENVIRONMENT_PATH.format(
            api_url=APIGEE_ADMIN_API_URL,
            org=self.org_name,
            environment=environment,
            name=self.map_name,
            entry_name=entry_name)
        return self.send_delete_request(uri)

    # ---- KVM CRUD ----
    def create_keyvaluemap_in_an_environment(self, environment, request_body):
        uri = CREATE_KEYVALUEMAP_IN_AN_ENVIRONMENT_PATH.format(
            api_url=APIGEE_ADMIN_API_URL,
            org=self.org_name,
            environment=environment)
        return _RequestHelper.post(self.auth,
                                   uri,
                                   json_body=json.loads(request_body))

    def update_keyvaluemap_in_an_environment(self, environment, request_body):
        uri = UPDATE_KEYVALUEMAP_IN_AN_ENVIRONMENT_PATH.format(
            api_url=APIGEE_ADMIN_API_URL,
            org=self.org_name,
            environment=environment,
            name=self.map_name)
        return _RequestHelper.post(self.auth,
                                   uri,
                                   json_body=json.loads(request_body))

    def delete_keyvaluemap_from_an_environment(self, environment):
        uri = DELETE_KEYVALUEMAP_FROM_AN_ENVIRONMENT_PATH.format(
            api_url=APIGEE_ADMIN_API_URL,
            org=self.org_name,
            environment=environment,
            name=self.map_name)
        return self.send_delete_request(uri)

    def send_delete_request(self, uri):
        return _RequestHelper.delete(self.auth, uri)

    # ---- Fetch / List ----
    def fetch_keys_in_environment_scoped_keyvaluemap(self, uri):
        return _RequestHelper.get(self.auth, uri)

    def get_a_keys_value_in_an_environment_scoped_keyvaluemap(
            self, environment, entry_name):
        uri = GET_A_KEYS_VALUE_IN_AN_ENVIRONMENT_SCOPED_KEYVALUEMAP_PATH.format(
            api_url=APIGEE_ADMIN_API_URL,
            org=self.org_name,
            environment=environment,
            name=self.map_name,
            entry_name=entry_name)
        return self.fetch_keys_in_environment_scoped_keyvaluemap(uri)

    def get_keyvaluemap_in_an_environment(self, environment):
        uri = GET_KEYVALUEMAP_IN_AN_ENVIRONMENT_PATH.format(
            api_url=APIGEE_ADMIN_API_URL,
            org=self.org_name,
            environment=environment,
            name=self.map_name)
        return self.fetch_keys_in_environment_scoped_keyvaluemap(uri)

    def list_keys_in_an_environment_scoped_keyvaluemap(self, environment,
                                                       startkey, count):
        uri = LIST_KEYS_IN_AN_ENVIRONMENT_SCOPED_KEYVALUEMAP_PATH.format(
            api_url=APIGEE_ADMIN_API_URL,
            org=self.org_name,
            environment=environment,
            name=self.map_name,
            startkey=startkey,
            count=count)
        return self.fetch_keys_in_environment_scoped_keyvaluemap(uri)

    def list_keyvaluemaps_in_an_environment(self,
                                            environment,
                                            prefix=None,
                                            format="json"):
        uri = LIST_KEYVALUEMAPS_IN_AN_ENVIRONMENT_PATH.format(
            api_url=APIGEE_ADMIN_API_URL,
            org=self.org_name,
            environment=environment)
        resp = self.fetch_keys_in_environment_scoped_keyvaluemap(uri)
        return KeyvaluemapsSerializer().serialize_details(resp,
                                                          format,
                                                          prefix=prefix)

    # ---- Encryption / Decryption ----
    @staticmethod
    def encrypt_keyvaluemap(kvm_dict, secret) -> Tuple[dict, int]:
        count = 0
        if not kvm_dict.get("entry"):
            return kvm_dict, count
        for i, entry in enumerate(kvm_dict["entry"]):
            if entry.get("name") and entry.get("value"):
                count += _EncryptionHelper.encrypt_entry(kvm_dict, i, secret)
        return kvm_dict, count

    @staticmethod
    def decrypt_keyvaluemap(kvm_dict, secret) -> Tuple[dict, int]:
        count = 0
        if not kvm_dict.get("entry"):
            return kvm_dict, count
        for i, entry in enumerate(kvm_dict["entry"]):
            if entry.get("name") and entry.get("value"):
                count += _EncryptionHelper.decrypt_entry(kvm_dict, i, secret)
        return kvm_dict, count

    # ---- Synchronization ----
    def delete_entries(self, environment, entries_to_delete):
        for entry in tqdm(entries_to_delete, **get_tqdm_kwargs("Deleting")):
            self.delete_keyvaluemap_entry_in_an_environment(
                environment, entry["name"])

    def synchronize_keyvaluemap_with_environment(self, environment, local_map):
        remote_map = self.get_keyvaluemap_in_an_environment(environment).json()
        deleted_keys = _SyncHelper.find_deleted_keys(local_map, remote_map)
        entries_to_update = _SyncHelper.entries_to_update(
            local_map, remote_map)

        if deleted_keys:
            self.delete_entries(environment, deleted_keys)
            console.echo("Removed entries.")
        if entries_to_update["entry"]:
            for entry in tqdm(entries_to_update["entry"],
                              **get_tqdm_kwargs("Updating")):
                self.create_or_update_entry(environment, entry)
            console.echo("Updated entries.")
        if not deleted_keys and not entries_to_update["entry"]:
            console.echo("All entries up-to-date.")

    # ---- Push from file ----
    def push_keyvaluemap(self, environment, file, secret=None):
        local_map = read_file_content(file, type="json")

        if secret:
            console.echo("Decrypting... ", line_ending="", should_flush=True)
            local_map, decrypted_count = Keyvaluemaps.decrypt_keyvaluemap(
                local_map, secret)
            console.echo("Done." if decrypted_count else "Nothing to decrypt.")
        elif any(
                has_encrypted_header(entry.get("value"))
                for entry in local_map.get("entry", [])):
            sys.exit(
                "KVM appears to be encrypted but no symmetric key (secret) was specified."
            )

        self.map_name = local_map["name"]
        try:
            self.synchronize_keyvaluemap_with_environment(
                environment, local_map)
        except HTTPError as e:
            if e.response.status_code != 404:
                raise
            console.echo(f"Creating {self.map_name}")
            console.echo(
                self.create_keyvaluemap_in_an_environment(
                    environment, json.dumps(local_map)).text)
