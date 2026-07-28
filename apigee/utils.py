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


def apply(iterable, func, state_op="append", args=(), kwargs=None):
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


def check_exists(file):
    if os.path.exists(file):
        sys.exit(f"error: {file} already exists")


def check_all_exist(files):
    for f in files:
        check_exists(f)


def mkdir(path):
    if path:
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            logging.warning(f"{inspect.stack()[0][3]}: failed to create directory", exc_info=True)


def touch(path):
    mkdir(os.path.dirname(path))

    try:
        if not os.path.exists(path):
            with open(path, "x"):
                pass
    except FileExistsError:
        logging.warning(f"{inspect.stack()[0][3]}: file already exists")


def remove_if_large(file, size_kb=100):
    if os.path.exists(file) and os.path.getsize(file) > size_kb * 1024:
        os.remove(file)


def is_dir(path):
    return os.path.isdir(path)


def is_file(path):
    return os.path.isfile(path)


def resolve_dir(target=None):
    if target:
        mkdir(target)
        return str(Path(target).resolve())

    return os.getcwd()


# --------------------
# io helpers
# --------------------


def read_file(file, type="text"):
    with open(file, "r") as f:
        return json.load(f) if type == "json" else f.read()


def write_file(content, path, write=True, indentation=None, append_eof=True):
    if not write:
        return

    touch(path)

    if isinstance(content, (dict, list)):
        content = json.dumps(content, indent=indentation) if isinstance(indentation, int) else json.dumps(content)

    if append_eof:
        content = f"{content}\n"

    with open(path, "w") as f:
        f.write(content)


def write_zip(file, content):
    touch(file)
    with open(file, "wb") as f:
        f.write(content)


def extract_zip(source, dest):
    with zipfile.ZipFile(source) as z:
        z.extractall(dest)


# --------------------
# collections
# --------------------


def as_set(iterable):
    return iterable if isinstance(iterable, set) else set(iterable)


def filter_empty(d):
    return {k: v for k, v in d.items() if v}


def merge_values(source, target=None):
    target = target or {}

    for k, v in source.items():
        if v:
            target[k] = v

    return target


def drop_last(lst, count=0):
    return lst if count <= 0 else lst[:-count]


# --------------------
# directory execution
# --------------------


def for_each_file(directory, func, glob="**/*", args=(), kwargs=None):
    kwargs = kwargs or {}
    results = []

    for path in Path(resolve_dir(directory)).glob(glob):
        result = func(str(path), *args, **kwargs)
        if result:
            results.append(result)

    return results


def load_plugins(init_file, commands):
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


def progress_opts(desc):
    return {
      "desc": desc,
      "unit": "entries",
      "bar_format": "{l_bar}{bar:32}{r_bar}{bar:-10b}",
      "leave": False,
    }


# def show_message(msg):
#     print(msg)

# def split_path(path, delimiter=r"[/\\\\]"):
#     return re.split(delimiter, path)
