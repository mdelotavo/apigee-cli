import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Set

from requests.exceptions import HTTPError
from tqdm import tqdm

from apigee import console
from apigee.apiproducts.apiproducts import Apiproducts
from apigee.apis.apis import Apis
from apigee.apps.apps import Apps
from apigee.caches.caches import Caches
from apigee.developers.developers import Developers
from apigee.exceptions import log_and_echo_http_error
from apigee.keyvaluemaps.keyvaluemaps import Keyvaluemaps
from apigee.permissions.permissions import Permissions
from apigee.targetservers.targetservers import Targetservers
from apigee.types import APIGEE_API_CHOICES, Struct, empty_snapshot
from apigee.userroles.userroles import Userroles
from apigee.utils import extract_zip_file, filter_out_empty_values, write_content_to_file

from .config import BackupConfig


class BaseBackup:

    def __init__(self, cfg: BackupConfig):
        self.cfg = cfg

    def save(self, content, subpath):
        path = self.cfg.working_org_directory
        for part in subpath.split("/"):
            path /= part
        write_content_to_file(content, path, indentation=2)

    def progress(self, label):
        if not isinstance(self.cfg.progress_bar, tqdm):
            self.cfg.progress_bar = tqdm(
              total=self.cfg.snapshot_size,
              unit="files",
              bar_format="{l_bar}{bar:32}{r_bar}{bar:-10b}",
              leave=False,
            )
        self.cfg.progress_bar.set_description(label)
        self.cfg.progress_bar.update(1)

    def http_error(self, e, msg):
        log_and_echo_http_error(e, append_message=msg)

    def error(self, e, *ctx):
        console.echo(type(e).__name__, *ctx)


class ApisBackup(BaseBackup):

    def collect(self):
        client = Apis(self.cfg.authentication, self.cfg.org_name)
        apis = client.list_api_proxies(prefix=self.cfg.prefix, format="dict")
        result = {}
        for api in apis:
            details = client.get_api_proxy(api).json()
            result[api] = details
            self.save(details, f"snapshots/apis/{api}.json")
        self.cfg.snapshot_data.apis = result

    def download(self):
        for api, meta in self.cfg.snapshot_data.apis.items():
            for rev in meta["revision"]:
                try:
                    output = Path(self.cfg.working_org_directory) / "apis" / api / rev / f"{api}.zip"
                    workdir = output.parent
                    Apis(self.cfg.authentication, self.cfg.org_name).export_api_proxy(api, rev, write_to_filesystem=True, output_file=str(output))
                    extract_zip_file(output, workdir)
                    os.remove(output)
                except HTTPError as e:
                    self.http_error(e, f" for API Proxy ({api}, revision {rev})")
                except Exception as e:
                    self.error(e, api, rev)
            self.progress("APIs")


class ApiProductsBackup(BaseBackup):

    def collect(self):
        products = Apiproducts(self.cfg.authentication, self.cfg.org_name, None).list_api_products(prefix=self.cfg.prefix, format="dict")
        self.cfg.snapshot_data.apiproducts = products
        self.save(products, "snapshots/apiproducts/apiproducts.json")

    def download(self):
        for name in self.cfg.snapshot_data.apiproducts:
            try:
                content = Apiproducts(self.cfg.authentication, self.cfg.org_name, name).get_api_product().text
                self.save(content, f"apiproducts/{name}.json")
            except HTTPError as e:
                self.http_error(e, f" for API Product ({name})")
            except Exception as e:
                self.error(e, name)
            self.progress("API Products")


class AppsBackup(BaseBackup):

    def collect(self):
        developers = Developers(self.cfg.authentication, self.cfg.org_name, None).list(format="dict")
        apps = Apps(self.cfg.authentication, self.cfg.org_name, None).list_all(developers, prefix=self.cfg.prefix, format="dict")
        apps = filter_out_empty_values(apps)
        self.cfg.snapshot_data.apps = apps
        for app, details in apps.items():
            self.save(details, f"snapshots/apps/{app}.json")

    def download(self):
        for dev, apps in self.cfg.snapshot_data.apps.items():
            for app in apps:
                try:
                    content = Apps(self.cfg.authentication, self.cfg.org_name, app).get(dev).text
                    self.save(content, f"apps/{dev}/{app}.json")
                except HTTPError as e:
                    self.http_error(e, f" for App ({app})")
                except Exception as e:
                    self.error(e, dev, app)
                self.progress("Apps")


class CachesBackup(BaseBackup):

    def collect(self):
        for env in self.cfg.environments:
            caches = Caches(self.cfg.authentication, self.cfg.org_name, None).list(env, prefix=self.cfg.prefix, format="dict")
            self.cfg.snapshot_data.caches[env] = caches
            self.save(caches, f"snapshots/caches/{env}/caches.json")

    def download(self):
        for env in self.cfg.environments:
            for cache in self.cfg.snapshot_data.caches[env]:
                try:
                    content = Caches(self.cfg.authentication, self.cfg.org_name, cache).get(env).text
                    self.save(content, f"caches/{env}/{cache}.json")
                except HTTPError as e:
                    self.http_error(e, f" for Cache ({cache})")
                except Exception as e:
                    self.error(e, env, cache)
                self.progress("Caches")


class DevelopersBackup(BaseBackup):

    def collect(self):
        devs = Developers(self.cfg.authentication, self.cfg.org_name, None).list(prefix=self.cfg.prefix, format="dict")
        self.cfg.snapshot_data.developers = devs
        self.save(devs, "snapshots/developers/developers.json")

    def download(self):
        for dev in self.cfg.snapshot_data.developers:
            try:
                content = Developers(self.cfg.authentication, self.cfg.org_name, dev).get().text
                self.save(content, f"developers/{dev}.json")
            except HTTPError as e:
                self.http_error(e, f" for Developer ({dev})")
            except Exception as e:
                self.error(e, dev)
            self.progress("Developers")


class KeyValueMapsBackup(BaseBackup):

    def collect(self):
        for env in self.cfg.environments:
            kvms = Keyvaluemaps(self.cfg.authentication, self.cfg.org_name, None).list_keyvaluemaps(env, prefix=self.cfg.prefix, format="dict")
            self.cfg.snapshot_data.keyvaluemaps[env] = kvms
            self.save(kvms, f"snapshots/keyvaluemaps/{env}/keyvaluemaps.json")

    def download(self):
        for env in self.cfg.environments:
            for kvm in self.cfg.snapshot_data.keyvaluemaps[env]:
                try:
                    content = Keyvaluemaps(self.cfg.authentication, self.cfg.org_name, kvm).get_keyvaluemap(env).text
                    self.save(content, f"keyvaluemaps/{env}/{kvm}.json")
                except HTTPError as e:
                    self.http_error(e, f" for KVM ({kvm})")
                except Exception as e:
                    self.error(e, env, kvm)
                self.progress("KeyValueMaps")


class TargetServersBackup(BaseBackup):

    def collect(self):
        for env in self.cfg.environments:
            targets = Targetservers(self.cfg.authentication, self.cfg.org_name, None).list(env, prefix=self.cfg.prefix, format="dict")
            self.cfg.snapshot_data.targetservers[env] = targets
            self.save(targets, f"snapshots/targetservers/{env}/targetservers.json")

    def download(self):
        for env in self.cfg.environments:
            for t in self.cfg.snapshot_data.targetservers[env]:
                try:
                    content = Targetservers(self.cfg.authentication, self.cfg.org_name, t).get(env).text
                    self.save(content, f"targetservers/{env}/{t}.json")
                except HTTPError as e:
                    self.http_error(e, f" for TargetServer ({t})")
                except Exception as e:
                    self.error(e, env, t)
                self.progress("TargetServers")


class UserRolesBackup(BaseBackup):

    def collect(self):
        roles = Userroles(self.cfg.authentication, self.cfg.org_name, None).list().json()
        if self.cfg.prefix:
            roles = [r for r in roles if r.startswith(self.cfg.prefix)]
        self.cfg.snapshot_data.userroles = roles
        self.save(roles, "snapshots/userroles/userroles.json")

    def download(self):
        for role in self.cfg.snapshot_data.userroles:
            try:
                ur = Userroles(self.cfg.authentication, self.cfg.org_name, role)
                users = ur.list_users().json()
                self.save(users, f"userroles/{role}/users.json")
                perms = Permissions(self.cfg.authentication, self.cfg.org_name, role).get(formatted=True, format="json")
                perms = Userroles.sort_resource_permissions(perms)
                self.save(json.dumps(perms, indent=2), f"userroles/{role}/resource_permissions.json")
            except HTTPError as e:
                self.http_error(e, f" for User Role ({role})")
            except Exception as e:

                import traceback
                traceback.print_exc()

                console.echo(f"{type(e).__name__}: {e}")
                self.error(e, role)
            self.progress("UserRoles")


class Backups:

    def __init__(self, cfg):
        self.cfg = cfg
        self.modules = {
          "apis": ApisBackup(cfg),
          "apiproducts": ApiProductsBackup(cfg),
          "apps": AppsBackup(cfg),
          "caches": CachesBackup(cfg),
          "developers": DevelopersBackup(cfg),
          "keyvaluemaps": KeyValueMapsBackup(cfg),
          "targetservers": TargetServersBackup(cfg),
          "userroles": UserRolesBackup(cfg),
        }

    def run(self):
        self._collect()
        self._calculate_size()
        self._download()
        if isinstance(self.cfg.progress_bar, tqdm):
            self.cfg.progress_bar.close()
        console.echo("Done.")

    def _collect(self):
        for name in self.cfg.api_choices:
            if name not in self.modules:
                continue
            console.echo(f"Retrieving {name} listing... ", line_ending="", should_flush=True)
            self.modules[name].collect()
            console.echo("Done")

    def _download(self):
        console.echo("Generating snapshot files...")
        for name in self.cfg.api_choices:
            if name not in self.modules:
                continue
            self.modules[name].download()

    def _calculate_size(self):
        total = 0
        data = self.cfg.snapshot_data.__dict__
        for key, val in data.items():
            if key == "apis":
                total += len(val)
            elif key in ("keyvaluemaps", "targetservers", "caches"):
                for _, env in val.items():
                    total += len(env)
            elif key == "apps":
                for _, apps in val.items():
                    total += len(apps)
            elif isinstance(val, list):
                total += len(val)
        self.cfg.snapshot_size = total
