import builtins
import sys


def echo(
  *message,
  exit_status=None,
  make_silent=False,
  current_verbosity=0,
  expected_verbosity=0,
  line_ending="\n",
  should_flush=False,
):
    if make_silent or builtins.APIGEE_CLI_TOGGLE_SILENT:
        if exit_status is not None:
            sys.exit(exit_status)
        return

    verbosity = max(current_verbosity, builtins.APIGEE_CLI_TOGGLE_VERBOSE)

    if verbosity >= expected_verbosity:
        print(*message, end=line_ending, flush=should_flush)

    if exit_status is not None:
        sys.exit(exit_status)
