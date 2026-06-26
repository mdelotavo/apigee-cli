from pathlib import Path

# A separate utils file which is referenced by __init__
# This file will be loaded and used by setup.py during apigee-cli installation, so it can only have
# references to the python standard library. Any other dependencies can cause the installation to fail,
# as those libraries may not be available prior to installation.


def join_path_components(*components):
    if not components:
        return ""

    return str(Path(components[0]).joinpath(*components[1:]))


def is_truthy_envvar(value):
    return str(value) in {"True", "true", "1"}
