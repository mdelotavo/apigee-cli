import json
import os
from typing import Any, List, Optional, Set, Dict
from dataclasses import dataclass, field
from pathlib import Path

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
from apigee.types import APIGEE_API_CHOICES, empty_snapshot, Struct
from apigee.userroles.userroles import Userroles
from apigee.utils import (
    extract_zip_file,
    filter_out_empty_values,
    get_resolved_directory_path,
    write_content_to_file,
)

# ==============================
# Path Templates
# ==============================
APIS_SNAPSHOT_TARGET_SUBPATH = "snapshots/apis/{api}.json"
KEYVALUEMAPS_SNAPSHOT_TARGET_SUBPATH = "snapshots/keyvaluemaps/{environment}/keyvaluemaps.json"
KEYVALUEMAPS_TARGET_SUBPATH = "keyvaluemaps/{environment}/{kvm}.json"
TARGETSERVERS_SNAPSHOT_TARGET_SUBPATH = "snapshots/targetservers/{environment}/targetservers.json"
TARGETSERVERS_TARGET_SUBPATH = "targetservers/{environment}/{targetserver}.json"
CACHES_SNAPSHOT_TARGET_SUBPATH = "snapshots/caches/{environment}/caches.json"
CACHES_TARGET_SUBPATH = "caches/{environment}/{cache}.json"
DEVELOPERS_SNAPSHOT_TARGET_SUBPATH = "snapshots/developers/developers.json"
DEVELOPERS_TARGET_SUBPATH = "developers/{developer}.json"
APIPRODUCTS_SNAPSHOT_TARGET_SUBPATH = "snapshots/apiproducts/apiproducts.json"
APIPRODUCTS_TARGET_SUBPATH = "apiproducts/{apiproduct}.json"
APPS_SNAPSHOT_TARGET_SUBPATH = "snapshots/apps/{app}.json"
APPS_TARGET_SUBPATH = "apps/{developer}/{app}.json"
USERROLES_SNAPSHOT_TARGET_SUBPATH = "snapshots/userroles/userroles.json"
USERROLES_FOR_A_ROLE_TARGET_SUBPATH = "userroles/{role_name}/users.json"
RESOURCE_PERMISSIONS_TARGET_SUBPATH = "userroles/{role_name}/resource_permissions.json"


# ==============================
# Configuration
# ==============================
@dataclass
class BackupConfig:
    api_choices: Set[str]
    authentication: Struct
    environments: List[str] = field(default_factory=list)
    org_name: str = ""
    prefix: Optional[str] = None
    working_directory: str = ""
    progress_bar: Any = None
    snapshot_data: Struct = field(default_factory=empty_snapshot)
    snapshot_size: int = 0
    working_org_directory: Optional[Path] = None

    def __post_init__(self):
        # Normalize and sort choices once
        self.api_choices = sorted(set(self.api_choices) if self.api_choices else APIGEE_API_CHOICES)
        # Resolve working paths once
        self.working_directory = get_resolved_directory_path(self.working_directory)
        self.working_org_directory = Path(self.working_directory) / self.org_name


# ==============================
# Helpers
# ==============================
class FileManager:
    @staticmethod
    def write(content: Any, base_path: Path, subpath: str, indentation: int = 2):
        full_path = FileManager.resolve(base_path, subpath)
        write_content_to_file(content, full_path, indentation=indentation)

    @staticmethod
    def resolve(base_path: Path, subpath: str) -> Path:
        full_path = base_path
        for part in subpath.split("/"):
            full_path /= part
        return full_path


class ProgressTracker:
    def __init__(self, config: BackupConfig):
        self.config = config

    def _ensure(self):
        if not isinstance(self.config.progress_bar, tqdm):
            self.config.progress_bar = tqdm(
                total=self.config.snapshot_size,
                unit="files",
                bar_format="{l_bar}{bar:32}{r_bar}{bar:-10b}",
                leave=False,
            )

    def update(self, description: str = ""):
        self._ensure()
        if description:
            self.config.progress_bar.set_description(description)
        self.config.progress_bar.update(1)

    def close(self):
        if self.config.progress_bar:
            self.config.progress_bar.close()


class ErrorHandler:
    @staticmethod
    def http(error: HTTPError, append_message: str):
        log_and_echo_http_error(error, append_message=append_message)

    @staticmethod
    def generic(exception: Exception, *args):
        console.echo(type(exception).__name__, *args)


# ==============================
# Resource Handlers (1 per domain)
# ==============================
class ApiHandler:
    def __init__(self, cfg: BackupConfig, fm: FileManager, progress: ProgressTracker):
        self.cfg = cfg
        self.fm = fm
        self.progress = progress

    # --- Snapshot ---
    def snapshot(self):
        api_list = self._list_apis()
        self.cfg.snapshot_data.apis = self._fetch_details(api_list)
        self._save_snapshot_files()

    def _list_apis(self) -> List[str]:
        return Apis(self.cfg.authentication, self.cfg.org_name).list_api_proxies(
            prefix=self.cfg.prefix, format="dict"
        )

    def _fetch_details(self, apis: List[str]) -> Dict[str, Dict]:
        result = {}
        for api in apis:
            result[api] = Apis(self.cfg.authentication, self.cfg.org_name).get_api_proxy(api).json()
        return result

    def _save_snapshot_files(self):
        for api, content in self.cfg.snapshot_data.apis.items():
            self.fm.write(content, self.cfg.working_org_directory, APIS_SNAPSHOT_TARGET_SUBPATH.format(api=api))

    # --- Download ---
    def download(self):
        for api, metadata in self.cfg.snapshot_data.apis.items():
            for revision in metadata.get("revision", []):
                output_file = str(Path(self.cfg.working_org_directory) / "apis" / api / revision / f"{api}.zip")
                work_dir = os.path.dirname(output_file)
                try:
                    Apis(self.cfg.authentication, self.cfg.org_name).export_api_proxy(
                        api,
                        revision,
                        write_to_filesystem=True,
                        output_file=output_file,
                    )
                    extract_zip_file(output_file, work_dir)
                    os.remove(output_file)
                except HTTPError as e:
                    ErrorHandler.http(e, append_message=f" for API Proxy ({api}, revision {revision})")
                except Exception as e:
                    ErrorHandler.generic(e, api, revision)
            self.progress.update("APIs")


class ApiProductHandler:
    def __init__(self, cfg: BackupConfig, fm: FileManager, progress: ProgressTracker):
        self.cfg = cfg
        self.fm = fm
        self.progress = progress

    # --- Snapshot ---
    def snapshot(self):
        apiproducts = Apiproducts(self.cfg.authentication, self.cfg.org_name, None).list_api_products(
            prefix=self.cfg.prefix, format="dict"
        )
        self.cfg.snapshot_data.apiproducts = apiproducts
        self.fm.write(apiproducts, self.cfg.working_org_directory, APIPRODUCTS_SNAPSHOT_TARGET_SUBPATH)

    # --- Download ---
    def download(self):
        for apiproduct in self.cfg.snapshot_data.apiproducts:
            try:
                content = (
                    Apiproducts(self.cfg.authentication, self.cfg.org_name, apiproduct)
                    .get_api_product()
                    .text
                )
                self.fm.write(content, self.cfg.working_org_directory, APIPRODUCTS_TARGET_SUBPATH.format(apiproduct=apiproduct))
            except HTTPError as e:
                ErrorHandler.http(e, append_message=f" for API Product ({apiproduct})")
            except Exception as e:
                ErrorHandler.generic(e, apiproduct)
            self.progress.update("API Products")


class AppHandler:
    def __init__(self, cfg: BackupConfig, fm: FileManager, progress: ProgressTracker):
        self.cfg = cfg
        self.fm = fm
        self.progress = progress

    # --- Snapshot ---
    def snapshot(self, expand: bool = False, count: int = 1000, startkey: str = ""):
        developers = Developers(self.cfg.authentication, self.cfg.org_name, None).list_developers(
            prefix=None, expand=expand, count=count, startkey=startkey, format="dict"
        )
        apps_by_developer = Apps(self.cfg.authentication, self.cfg.org_name, None).list_apps_for_all_developers(
            developers, prefix=self.cfg.prefix, format="dict"
        )
        apps_by_developer = filter_out_empty_values(apps_by_developer)
        self.cfg.snapshot_data.apps = apps_by_developer

        for app_name, details in apps_by_developer.items():
            self.fm.write(details, self.cfg.working_org_directory, APPS_SNAPSHOT_TARGET_SUBPATH.format(app=app_name))

    # --- Download ---
    def download(self):
        for developer, apps in self.cfg.snapshot_data.apps.items():
            for app in apps:
                try:
                    content = (
                        Apps(self.cfg.authentication, self.cfg.org_name, app)
                        .get_developer_app_details(developer)
                        .text
                    )
                    self.fm.write(content, self.cfg.working_org_directory, APPS_TARGET_SUBPATH.format(developer=developer, app=app))
                except HTTPError as e:
                    ErrorHandler.http(e, append_message=f" for Developer App ({app})")
                except Exception as e:
                    ErrorHandler.generic(e, developer, app)
                self.progress.update("Developer Apps")


class CacheHandler:
    def __init__(self, cfg: BackupConfig, fm: FileManager, progress: ProgressTracker):
        self.cfg = cfg
        self.fm = fm
        self.progress = progress

    # --- Snapshot ---
    def snapshot(self):
        for environment in self.cfg.environments:
            caches = Caches(self.cfg.authentication, self.cfg.org_name, None).list_caches_in_an_environment(
                environment, prefix=self.cfg.prefix, format="dict"
            )
            self.cfg.snapshot_data.caches[environment] = caches
            self.fm.write(caches, self.cfg.working_org_directory, CACHES_SNAPSHOT_TARGET_SUBPATH.format(environment=environment))

    # --- Download ---
    def download(self):
        for environment in self.cfg.environments:
            caches = self.cfg.snapshot_data.caches.get(environment, [])
            for cache in caches:
                try:
                    content = (
                        Caches(self.cfg.authentication, self.cfg.org_name, cache)
                        .get_information_about_a_cache(environment)
                        .text
                    )
                    self.fm.write(content, self.cfg.working_org_directory, CACHES_TARGET_SUBPATH.format(environment=environment, cache=cache))
                except HTTPError as e:
                    ErrorHandler.http(e, append_message=f" for Cache ({cache})")
                except Exception as e:
                    ErrorHandler.generic(e, environment, cache)
                self.progress.update("Caches")


class DeveloperHandler:
    def __init__(self, cfg: BackupConfig, fm: FileManager, progress: ProgressTracker):
        self.cfg = cfg
        self.fm = fm
        self.progress = progress

    # --- Snapshot ---
    def snapshot(self):
        developers = Developers(self.cfg.authentication, self.cfg.org_name, None).list_developers(
            prefix=self.cfg.prefix, format="dict"
        )
        self.cfg.snapshot_data.developers = developers
        self.fm.write(developers, self.cfg.working_org_directory, DEVELOPERS_SNAPSHOT_TARGET_SUBPATH)

    # --- Download ---
    def download(self):
        for developer in self.cfg.snapshot_data.developers:
            try:
                content = (
                    Developers(self.cfg.authentication, self.cfg.org_name, developer)
                    .get_developer()
                    .text
                )
                self.fm.write(content, self.cfg.working_org_directory, DEVELOPERS_TARGET_SUBPATH.format(developer=developer))
            except HTTPError as e:
                ErrorHandler.http(e, append_message=f" for Developer ({developer})")
            except Exception as e:
                ErrorHandler.generic(e, developer)
            self.progress.update("Developers")


class KeyValueMapHandler:
    def __init__(self, cfg: BackupConfig, fm: FileManager, progress: ProgressTracker):
        self.cfg = cfg
        self.fm = fm
        self.progress = progress

    # --- Snapshot ---
    def snapshot(self):
        for environment in self.cfg.environments:
            kvms = Keyvaluemaps(self.cfg.authentication, self.cfg.org_name, None).list_keyvaluemaps_in_an_environment(
                environment, prefix=self.cfg.prefix, format="dict"
            )
            self.cfg.snapshot_data.keyvaluemaps[environment] = kvms
            self.fm.write(kvms, self.cfg.working_org_directory, KEYVALUEMAPS_SNAPSHOT_TARGET_SUBPATH.format(environment=environment))

    # --- Download ---
    def download(self):
        for environment in self.cfg.environments:
            kvms = self.cfg.snapshot_data.keyvaluemaps.get(environment, [])
            for kvm in kvms:
                try:
                    content = (
                        Keyvaluemaps(self.cfg.authentication, self.cfg.org_name, kvm)
                        .get_keyvaluemap_in_an_environment(environment)
                        .text
                    )
                    self.fm.write(content, self.cfg.working_org_directory, KEYVALUEMAPS_TARGET_SUBPATH.format(environment=environment, kvm=kvm))
                except HTTPError as e:
                    ErrorHandler.http(e, append_message=f" for KVM ({kvm})")
                except Exception as e:
                    ErrorHandler.generic(e, environment, kvm)
                self.progress.update("KeyValueMaps")


class TargetServerHandler:
    def __init__(self, cfg: BackupConfig, fm: FileManager, progress: ProgressTracker):
        self.cfg = cfg
        self.fm = fm
        self.progress = progress

    # --- Snapshot ---
    def snapshot(self):
        for environment in self.cfg.environments:
            targetservers = Targetservers(self.cfg.authentication, self.cfg.org_name, None).list_targetservers_in_an_environment(
                environment, prefix=self.cfg.prefix, format="dict"
            )
            self.cfg.snapshot_data.targetservers[environment] = targetservers
            self.fm.write(
                targetservers,
                self.cfg.working_org_directory,
                TARGETSERVERS_SNAPSHOT_TARGET_SUBPATH.format(environment=environment),
            )

    # --- Download ---
    def download(self):
        for environment in self.cfg.environments:
            targetservers = self.cfg.snapshot_data.targetservers.get(environment, [])
            for targetserver in targetservers:
                try:
                    content = (
                        Targetservers(self.cfg.authentication, self.cfg.org_name, targetserver)
                        .get_targetserver(environment)
                        .text
                    )
                    self.fm.write(
                        content,
                        self.cfg.working_org_directory,
                        TARGETSERVERS_TARGET_SUBPATH.format(environment=environment, targetserver=targetserver),
                    )
                except HTTPError as e:
                    ErrorHandler.http(e, append_message=f" for TargetServer ({targetserver})")
                except Exception as e:
                    ErrorHandler.generic(e, environment, targetserver)
                self.progress.update("TargetServers")


class UserRoleHandler:
    def __init__(self, cfg: BackupConfig, fm: FileManager, progress: ProgressTracker):
        self.cfg = cfg
        self.fm = fm
        self.progress = progress

    # --- Snapshot ---
    def snapshot(self):
        roles = Userroles(self.cfg.authentication, self.cfg.org_name, None).list_user_roles().json()
        if self.cfg.prefix:
            roles = [r for r in roles if r.startswith(self.cfg.prefix)]
        self.cfg.snapshot_data.userroles = roles
        self.fm.write(roles, self.cfg.working_org_directory, USERROLES_SNAPSHOT_TARGET_SUBPATH)

    # --- Download ---
    def download(self):
        for role_name in self.cfg.snapshot_data.userroles:
            try:
                users_content = (
                    Userroles(self.cfg.authentication, self.cfg.org_name, role_name)
                    .get_users_for_a_role()
                    .json()
                )
                self.fm.write(users_content, self.cfg.working_org_directory, USERROLES_FOR_A_ROLE_TARGET_SUBPATH.format(role_name=role_name))
            except HTTPError as e:
                ErrorHandler.http(e, append_message=" for User Role ({role_name}) users")
            except Exception as e:
                ErrorHandler.generic(e, role_name)

            try:
                permissions = Permissions(self.cfg.authentication, self.cfg.org_name, role_name).get_permissions(
                    formatted=True, format="json"
                )
                content = Userroles.sort_resource_permissions(permissions)
                self.fm.write(json.dumps(content, indent=2), self.cfg.working_org_directory, RESOURCE_PERMISSIONS_TARGET_SUBPATH.format(role_name=role_name))
            except HTTPError as e:
                ErrorHandler.http(e, append_message=" for User Role ({role_name}) resource permissions")
            except Exception as e:
                ErrorHandler.generic(e, role_name, "(resource permissions)")

            self.progress.update("User Roles")


# ==============================
# Orchestration (replaces Backups)
# ==============================
class BackupCoordinator:
    """
    Coordinates snapshot generation and downloads.
    Mirrors the original class behavior but with clearer structure and names.
    """

    def __init__(self, config: BackupConfig):
        self.cfg = config
        self.fm = FileManager()
        self.progress = ProgressTracker(self.cfg)

        # Handlers per domain
        self.api_handler = ApiHandler(self.cfg, self.fm, self.progress)
        self.apiproduct_handler = ApiProductHandler(self.cfg, self.fm, self.progress)
        self.app_handler = AppHandler(self.cfg, self.fm, self.progress)
        self.cache_handler = CacheHandler(self.cfg, self.fm, self.progress)
        self.developer_handler = DeveloperHandler(self.cfg, self.fm, self.progress)
        self.kvm_handler = KeyValueMapHandler(self.cfg, self.fm, self.progress)
        self.targetserver_handler = TargetServerHandler(self.cfg, self.fm, self.progress)
        self.userrole_handler = UserRoleHandler(self.cfg, self.fm, self.progress)

    # ---------- Public entry points (compat with original intent) ----------

    def generate_snapshot_files_and_download_data(self):
        """
        Original combined orchestration: create listings, snapshot files, then download configs.
        """
        self.fetch_and_generate_snapshots()
        self.generate_snapshot_files()
        self.close_progress_bar()
        console.echo("Done.")

    def fetch_and_generate_snapshots(self):
        """
        Generate in-memory snapshots for each selected API choice.
        """
        for api_choice in self.cfg.api_choices:
            self._echo_retrieving(api_choice)
            self._snapshot_dispatch(api_choice)
            console.echo("Done")
        self.cfg.snapshot_size = self._count_snapshot_items()

    def generate_snapshot_files(self):
        """
        Download and write each resource's full configuration data to disk.
        """
        console.echo("Generating snapshot files...")
        for api_choice in self.cfg.api_choices:
            self._download_dispatch(api_choice)

    def close_progress_bar(self):
        self.progress.close()

    # ---------- Internal helpers ----------

    def _echo_retrieving(self, api_choice: str):
        long_running = api_choice in ("apis", "apps")
        message = f"Retrieving {api_choice} listing{' (this may take a while)' if long_running else ''}... "
        console.echo(message, line_ending="", should_flush=True)

    def _snapshot_dispatch(self, api_choice: str):
        # Map to handler snapshot methods
        mapping = {
            "apis": self.api_handler.snapshot,
            "apiproducts": self.apiproduct_handler.snapshot,
            "apps": self.app_handler.snapshot,
            "caches": self.cache_handler.snapshot,
            "developers": self.developer_handler.snapshot,
            "keyvaluemaps": self.kvm_handler.snapshot,
            "targetservers": self.targetserver_handler.snapshot,
            "userroles": self.userrole_handler.snapshot,
        }
        if api_choice not in mapping:
            raise ValueError(f"Unsupported api_choice for snapshot: {api_choice}")
        mapping[api_choice]()

    def _download_dispatch(self, api_choice: str):
        # Map to handler download methods
        mapping = {
            "apis": self.api_handler.download,
            "apiproducts": self.apiproduct_handler.download,
            "apps": self.app_handler.download,
            "caches": self.cache_handler.download,
            "developers": self.developer_handler.download,
            "keyvaluemaps": self.kvm_handler.download,
            "targetservers": self.targetserver_handler.download,
            "userroles": self.userrole_handler.download,
        }
        if api_choice not in mapping:
            raise ValueError(f"Unsupported api_choice for download: {api_choice}")
        mapping[api_choice]()

    def _count_snapshot_items(self) -> int:
        """
        Mirrors calculate_total_snapshot_size from original, but clearer.
        """
        total_size = 0
        data = self.cfg.snapshot_data.__dict__
        for key, value in data.items():
            if key == "apis" and isinstance(value, dict):
                total_size += len(value)
            elif key in ("keyvaluemaps", "targetservers", "caches") and isinstance(value, dict):
                for _, env_items in value.items():
                    total_size += len(env_items)
            elif key == "apps" and isinstance(value, dict):
                for _, apps in value.items():
                    total_size += len(apps)
            elif isinstance(value, list):
                total_size += len(value)
        return total_size


# ==============================
# Backwards-compatible aliases
# ==============================
# If other modules import `Backups`, keep a thin wrapper that delegates to the coordinator.
class Backups:
    """
    Backwards-compatible adapter that preserves the original class name.
    Internally delegates to BackupCoordinator with the same behavior.
    """

    def __init__(self, config: BackupConfig):
        self._coordinator = BackupCoordinator(config)

    # Original public methods mapped directly
    def generate_snapshot_files_and_download_data(self):
        self._coordinator.generate_snapshot_files_and_download_data()

    def fetch_and_generate_snapshots(self):
        self._coordinator.fetch_and_generate_snapshots()

    def generate_snapshot_files(self):
        self._coordinator.generate_snapshot_files()

    def close_progress_bar(self):
        self._coordinator.close_progress_bar()

    # (Optional) Provide access to config if callers used it directly
    @property
    def backupConfig(self) -> BackupConfig:
        return self._coordinator.cfg
