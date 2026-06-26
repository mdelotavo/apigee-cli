import logging
import os
import xml.etree.ElementTree as et
from pathlib import Path

from apigee import console
from apigee.apis.apis import Apis
from apigee.caches.caches import Caches
from apigee.keyvaluemaps.keyvaluemaps import Keyvaluemaps
from apigee.targetservers.targetservers import Targetservers
from apigee.utils import (
  apply_function_on_iterable,
  check_file_exists,
  check_files_exist,
  create_directory,
  execute_function_on_directory_files,
  extract_zip_file,
)


class ApiBundleExporter:

    def __init__(self, auth, org_name, revision, environment, working_directory=None):
        self.auth = auth
        self.org_name = org_name
        self.revision = revision
        self.environment = environment

        self.root = Path(working_directory or os.getcwd()).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

        self.apiproxy_dir = self.root
        self.kvm_dir = self.root / "keyvaluemaps" / environment
        self.target_dir = self.root / "targetservers" / environment
        self.cache_dir = self.root / "caches" / environment

    def export(self, api_name, force=False):
        zip_file = str((self.apiproxy_dir / api_name).with_suffix(".zip"))
        api_dir = self.apiproxy_dir / api_name

        if not force:
            check_files_exist((os.path.relpath(zip_file), os.path.relpath(api_dir)))

        create_directory(str(self.root))

        exported = Apis(self.auth, self.org_name).export_api_proxy(api_name, self.revision, write_to_filesystem=True, output_file=zip_file)

        create_directory(str(api_dir))
        extract_zip_file(zip_file, str(api_dir))
        os.remove(zip_file)

        files = self._apiproxy_files(api_dir)

        self._export_deps(self._get_kvms(files), self._write_kvm, force)
        self._export_deps(self._get_targets(files), self._write_target, force)
        self._export_deps(self._get_caches(files), self._write_cache, force)

        return exported

    def _export_deps(self, items, fn, force):
        return apply_function_on_iterable(items, lambda x: fn(x, force))

    def _write_cache(self, name, force):
        path = self.cache_dir / f"{name}.json"
        create_directory(str(self.cache_dir))

        if not force:
            check_file_exists(os.path.relpath(path))

        resp = Caches(self.auth, self.org_name, name).get_information_about_a_cache(self.environment).text
        console.echo(resp, expected_verbosity=1)
        path.write_text(resp)

    def _write_kvm(self, name, force):
        path = self.kvm_dir / f"{name}.json"
        create_directory(str(self.kvm_dir))

        if not force:
            check_file_exists(os.path.relpath(path))

        resp = Keyvaluemaps(self.auth, self.org_name, name).get_keyvaluemap(self.environment).text
        console.echo(resp, expected_verbosity=1)
        path.write_text(resp)

    def _write_target(self, name, force):
        path = self.target_dir / f"{name}.json"
        create_directory(str(self.target_dir))

        if not force:
            check_file_exists(os.path.relpath(path))

        resp = Targetservers(self.auth, self.org_name, name).get_targetserver(self.environment).text
        console.echo(resp, expected_verbosity=1)
        path.write_text(resp)

    def _apiproxy_files(self, directory):
        return execute_function_on_directory_files(str(Path(directory) / "apiproxy"), lambda f: f)

    def _get_caches(self, files):

        def fn(f, seen):
            try:
                name = et.parse(f).find(".//CacheResource").text
                if name and name not in seen:
                    seen.add(name)
                    return name
            except Exception as e:
                logging.warning(f"{e}; file={f}", exc_info=True)

        return apply_function_on_iterable(files, fn, args=(set(), ))

    def _get_kvms(self, files):

        def fn(f, seen):
            try:
                root = et.parse(f).getroot()
                if root.tag == "KeyValueMapOperations":
                    name = root.attrib["mapIdentifier"]
                    if name not in seen:
                        seen.add(name)
                        return name
            except Exception as e:
                logging.warning(f"{e}; file={f}", exc_info=True)

        return apply_function_on_iterable(files, fn, args=(set(), ))

    def _get_targets(self, files):

        def fn(f, seen):
            try:
                root = et.parse(f).getroot()
                for srv in root.iter("Server"):
                    name = srv.attrib["name"]
                    if name not in seen:
                        seen.add(name)
                        return name
            except Exception as e:
                logging.warning(f"{e}; file={f}", exc_info=True)

        return apply_function_on_iterable(files, fn, args=(set(), ))
