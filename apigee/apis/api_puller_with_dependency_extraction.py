import logging
import os
import xml.etree.ElementTree as et
from pathlib import Path

from apigee import console
from apigee.apis.apis import Apis
from apigee.caches.caches import Caches
from apigee.keyvaluemaps.keyvaluemaps import Keyvaluemaps
from apigee.targetservers.targetservers import Targetservers
from apigee.utils import (apply_function_on_iterable, check_file_exists,
                          check_files_exist, create_directory,
                          execute_function_on_directory_files,
                          extract_zip_file)

# ---------------------------
# Internal Helper for XML Parsing
# ---------------------------


class _SyncHelper:

    @staticmethod
    def extract_cache_dependencies(file, _state):
        try:
            name = et.parse(file).find(".//CacheResource").text
            if name and name not in _state:
                _state.add(name)
                return name
        except Exception as e:
            logging.warning(f"{e}; file={file}", exc_info=True)

    @staticmethod
    def extract_keyvaluemap_dependencies(file, _state):
        try:
            root = et.parse(file).getroot()
            if root.tag == "KeyValueMapOperations":
                map_id = root.attrib["mapIdentifier"]
                if map_id not in _state:
                    _state.add(map_id)
                    return map_id
        except Exception as e:
            logging.warning(f"{e}; file={file}", exc_info=True)

    @staticmethod
    def extract_targetserver_dependencies(file, _state):
        try:
            root = et.parse(file).getroot()
            for child in root.iter("Server"):
                name = child.attrib["name"]
                if name not in _state:
                    _state.add(name)
                    return name
        except Exception as e:
            logging.warning(f"{e}; file={file}", exc_info=True)


# ---------------------------
# Resource Exporter Classes
# ---------------------------


class KeyValueMapsExporter:

    def __init__(self, auth, org_name, environment, output_dir):
        self.auth = auth
        self.org_name = org_name
        self.environment = environment
        self.output_dir = Path(output_dir) / environment
        create_directory(self.output_dir)

    def export(self, keyvaluemaps, force=False, expected_verbosity=1):

        def _func(kvm):
            kvm_file = self.output_dir / f"{kvm}.json"
            if not force:
                check_file_exists(os.path.relpath(kvm_file))
            resp = Keyvaluemaps(self.auth, self.org_name,
                                kvm).get_keyvaluemap_in_an_environment(
                                    self.environment).text
            console.echo(resp, expected_verbosity=expected_verbosity)
            with open(kvm_file, "w") as f:
                f.write(resp)

        return apply_function_on_iterable(keyvaluemaps, _func)

    def get_dependencies(self, files):
        return apply_function_on_iterable(
            files,
            _SyncHelper.extract_keyvaluemap_dependencies,
            args=(set(), ))


class CachesExporter:

    def __init__(self, auth, org_name, environment, output_dir):
        self.auth = auth
        self.org_name = org_name
        self.environment = environment
        self.output_dir = Path(output_dir) / environment
        create_directory(self.output_dir)

    def export(self, caches, force=False, expected_verbosity=1):

        def _func(cache):
            cache_file = self.output_dir / f"{cache}.json"
            if not force:
                check_file_exists(os.path.relpath(cache_file))
            resp = Caches(self.auth, self.org_name,
                          cache).get_information_about_a_cache(
                              self.environment).text
            console.echo(resp, expected_verbosity=expected_verbosity)
            with open(cache_file, "w") as f:
                f.write(resp)

        return apply_function_on_iterable(caches, _func)

    def get_dependencies(self, files):
        return apply_function_on_iterable(
            files, _SyncHelper.extract_cache_dependencies, args=(set(), ))


class TargetServersExporter:

    def __init__(self, auth, org_name, environment, output_dir):
        self.auth = auth
        self.org_name = org_name
        self.environment = environment
        self.output_dir = Path(output_dir) / environment
        create_directory(self.output_dir)

    def export(self, targetservers, force=False, expected_verbosity=1):

        def _func(ts):
            ts_file = self.output_dir / f"{ts}.json"
            if not force:
                check_file_exists(os.path.relpath(ts_file))
            resp = Targetservers(self.auth, self.org_name,
                                 ts).get_targetserver(self.environment).text
            console.echo(resp, expected_verbosity=expected_verbosity)
            with open(ts_file, "w") as f:
                f.write(resp)

        return apply_function_on_iterable(targetservers, _func)

    def get_dependencies(self, files):
        return apply_function_on_iterable(
            files,
            _SyncHelper.extract_targetserver_dependencies,
            args=(set(), ))


# ---------------------------
# Main API Puller
# ---------------------------


class ApiPullerWithDependencyExtraction:
    """
    Orchestrates exporting an API proxy along with all dependent resources.
    """

    def __init__(self,
                 auth,
                 org_name,
                 revision_number,
                 environment,
                 working_directory=None):
        self.auth = auth
        self.org_name = org_name
        self.revision_number = revision_number
        self.environment = environment
        self.working_directory = Path(working_directory or os.getcwd())

        # Initialize resource exporters
        self.keyvaluemaps_exporter = KeyValueMapsExporter(
            auth, org_name, environment,
            self.working_directory / "keyvaluemaps")
        self.caches_exporter = CachesExporter(
            auth, org_name, environment, self.working_directory / "caches")
        self.targetservers_exporter = TargetServersExporter(
            auth, org_name, environment,
            self.working_directory / "targetservers")

        self.apiproxy_dir = self.working_directory
        self.zip_file = self.working_directory.with_suffix(".zip")

    # ---------------------------
    # API Proxy Extraction
    # ---------------------------

    def export_and_extract_api_proxy(self, api_name, force=False):
        create_directory(self.working_directory)
        self.apiproxy_dir = self.working_directory / api_name

        if not force:
            check_files_exist((os.path.relpath(self.zip_file),
                               os.path.relpath(self.apiproxy_dir)))

        exported_api = Apis(self.auth, self.org_name).export_api_proxy(
            api_name,
            self.revision_number,
            write_to_filesystem=True,
            output_file=str(self.zip_file))

        create_directory(self.apiproxy_dir)
        extract_zip_file(str(self.zip_file), str(self.apiproxy_dir))
        os.remove(self.zip_file)

        files = self.get_apiproxy_files(self.apiproxy_dir)
        for resource_type in ("keyvaluemap", "targetserver", "cache"):
            self.export_resource_dependencies(resource_type,
                                              files,
                                              force=force)

        return exported_api

    # ---------------------------
    # Resource Dependency Orchestration
    # ---------------------------

    def export_resource_dependencies(self, resource_type, files, force=True):
        exporter_map = {
            "keyvaluemap": self.keyvaluemaps_exporter,
            "cache": self.caches_exporter,
            "targetserver": self.targetservers_exporter,
        }
        exporter = exporter_map[resource_type]
        resource_files = exporter.get_dependencies(files)
        exporter.export(resource_files, force=force)
        return resource_files

    def get_apiproxy_files(self, directory):
        return execute_function_on_directory_files(
            str(Path(directory) / "apiproxy"), lambda f: f)
