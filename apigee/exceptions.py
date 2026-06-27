import functools
import inspect
import logging
import sys

from apigee import console
from apigee.utils import create_empty_file, remove_file_if_above_size


class InvalidApisError(Exception):
    pass


# --------------------
# logging
# --------------------


def configure_global_logger(log_file):
    create_empty_file(log_file)
    remove_file_if_above_size(log_file, size_kb=1000)

    logging.basicConfig(
      filename=log_file,
      level=logging.WARNING,
      format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def log_and_echo_http_error(error, append_message=""):
    msg = f"Ignoring {type(error).__name__} {error.response.status_code} error{append_message}"
    logging.warning(msg)
    console.echo(msg)


# --------------------
# exception wrapper
# --------------------


def wrap_with_exception_handling(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except KeyboardInterrupt:
            console.echo()
            sys.exit(130)

        except Exception as e:
            logging.error("Exception occurred", exc_info=True)

            frame = inspect.trace()[-1]
            module = inspect.getmodule(frame[0])
            module_name = module.__name__ if module else frame.filename

            sys.exit(f"An exception of type {module_name}.{type(e).__name__} occurred.\n"
                     f"Arguments:\n{e}")

    return wrapper
