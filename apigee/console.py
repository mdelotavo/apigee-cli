import builtins
import sys
from dataclasses import dataclass, fields, replace


@dataclass(slots=True)
class EchoOptions:
    exit_status: int | None = None
    silent: bool = False
    verbosity: int = 0
    level: int = 0
    end: str = "\n"
    flush: bool = False


def echo(*msg, options: EchoOptions | None = None, **kwargs):
    options = options or EchoOptions()

    valid_fields = {f.name for f in fields(EchoOptions)}

    for key, value in kwargs.items():
        if key not in valid_fields:
            raise TypeError(f"echo() got an unexpected keyword argument '{key}'")
        options = replace(options, **{key: value})

    if options.silent or builtins.APIGEE_CLI_TOGGLE_SILENT:
        if options.exit_status is not None:
            sys.exit(options.exit_status)
        return

    verbosity = max(options.verbosity, builtins.APIGEE_CLI_TOGGLE_VERBOSE)

    if verbosity >= options.level:
        print(*msg, end=options.end, flush=options.flush)

    if options.exit_status is not None:
        sys.exit(options.exit_status)