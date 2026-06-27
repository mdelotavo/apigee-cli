#!/usr/bin/env python3
import re
import argparse
from pathlib import Path

VERSION_REGEX = re.compile(
    r'^(?P<indent>\s*)(?P<var>__version__|version)\s*=\s*["\'](?P<version>\d+\.\d+\.\d+)["\']',
    re.MULTILINE)


def bump_version(match, part):
    major, minor, patch = map(int, match.group("version").split("."))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    return f'{match.group("indent")}{match.group("var")} = "{major}.{minor}.{patch}"'


def process_file(path, part):
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    new_content = VERSION_REGEX.sub(lambda m: bump_version(m, part), content)
    path.write_text(new_content, encoding="utf-8")
    print(f"Updated {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Bump semantic versions in version or __version__ variables"
    )
    parser.add_argument("part",
                        choices=["major", "minor", "patch"],
                        help="Which version part to bump")
    parser.add_argument("files", nargs="+", help="Files to update")
    args = parser.parse_args()

    for file in args.files:
        process_file(file, args.part)


if __name__ == "__main__":
    main()

# python bump_version.py minor apigee/__init__.py pyproject.toml
# python ./tools/bump_version.py minor apigee/__init__.py pyproject.toml
