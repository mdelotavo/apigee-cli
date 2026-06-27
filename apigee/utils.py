import importlib.util
import inspect
import json
import logging
import os
import re
import sys
import zipfile
from pathlib import Path

import click

# --------------------
# iteration helpers
# --------------------


def apply_function_on_iterable(iterable, func, state_op="append", args=(), kwargs=None):
    kwargs = kwargs or {}
    state = []

    for item in iterable:
        result = func(item, *args, **kwargs)
        if result:
            getattr(state, state_op)(result)

    return state


# --------------------
# filesystem helpers
# --------------------


def check_file_exists(file):
    if os.path.exists(file):
        sys.exit(f"error: {file} already exists")


def check_files_exist(files):
    for f in files:
        check_file_exists(f)


def create_directory(path):
    if path:
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            logging.warning(f"{inspect.stack()[0][3]}: failed to create directory", exc_info=True)


def create_empty_file(path):
    create_directory(os.path.dirname(path))

    try:
        if not os.path.exists(path):
            with open(path, "x"):
                pass
    except FileExistsError:
        logging.warning(f"{inspect.stack()[0][3]}: file already exists")


def remove_file_if_above_size(file, size_kb=100):
    if os.path.exists(file) and os.path.getsize(file) > size_kb * 1024:
        os.remove(file)


def is_directory(path):
    return os.path.isdir(path)


def is_regular_file(path):
    return os.path.isfile(path)


def get_resolved_directory_path(target=None):
    if target:
        create_directory(target)
        return str(Path(target).resolve())

    return os.getcwd()


# --------------------
# io helpers
# --------------------


def read_file_content(file, type="text"):
    with open(file, "r") as f:
        return json.load(f) if type == "json" else f.read()


def write_content_to_file(content, path, write=True, indentation=None, append_eof=True):
    if not write:
        return

    create_empty_file(path)

    if isinstance(content, (dict, list)):
        content = json.dumps(content, indent=indentation) if isinstance(indentation, int) else json.dumps(content)

    if append_eof:
        content = f"{content}\n"

    with open(path, "w") as f:
        f.write(content)


def write_content_to_zip(file, content):
    create_empty_file(file)
    with open(file, "wb") as f:
        f.write(content)


def extract_zip_file(source, dest):
    with zipfile.ZipFile(source) as z:
        z.extractall(dest)


# --------------------
# collections
# --------------------


def ensure_set(iterable):
    return iterable if isinstance(iterable, set) else set(iterable)


def filter_out_empty_values(data):
    return {k: v for k, v in data.items() if v}


def merge_dict_values(source, target=None):
    target = target or {}

    for k, v in source.items():
        if v:
            target[k] = v

    return target


def remove_last_elements(items, count=0):
    return items if count <= 0 else items[:-count]


# --------------------
# directory execution
# --------------------


def execute_function_on_directory_files(directory, func, glob="**/*", args=(), kwargs=None):
    kwargs = kwargs or {}
    results = []

    for path in Path(get_resolved_directory_path(directory)).glob(glob):
        result = func(str(path), *args, **kwargs)
        if result:
            results.append(result)

    return results


def import_plugins_from_directory(init_file, commands):
    try:
        spec = importlib.util.spec_from_file_location("plugins_modules", init_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        plugins = getattr(module, "__all__", [])

        for name in plugins:
            obj = getattr(module, name)
            if isinstance(obj, (click.Command, click.Group)):
                commands.add(obj)

    except ImportError:
        logging.warning("Failed to load plugin", exc_info=True)


# --------------------
# misc
# --------------------


def get_progress_kwargs(desc):
    return {
      "desc": desc,
      "unit": "entries",
      "bar_format": "{l_bar}{bar:32}{r_bar}{bar:-10b}",
      "leave": False,
    }


def show_message(msg):
    print(msg)


def split_path_by_delimiter(path, delimiter=r"[/\\\\]"):
    return re.split(delimiter, path)
