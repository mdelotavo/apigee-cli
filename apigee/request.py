import json
from urllib.parse import quote_plus

import requests

from apigee import APIGEE_CLI_ENABLE_SSL_VERIFY as VERIFY_SSL
from apigee import APIGEE_QUERY_PARAMETERS, auth

import urllib3

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_HEADERS = {"Accept": "application/json"}


def request(method, uri, auth_object, headers=None, raise_exception=True, **kwargs):
    if APIGEE_QUERY_PARAMETERS:
        try:
            query_parameters = json.loads(APIGEE_QUERY_PARAMETERS)
            if query_parameters and isinstance(query_parameters, dict):
                additional_parameters = [quote_plus(key) + "=" + quote_plus(query_parameters[key]) for key in query_parameters]
                uri += ("?" if "?" not in uri else "&") + "&".join(additional_parameters)
        except:
            pass

    custom_headers = DEFAULT_HEADERS if headers is None else headers
    request_headers = auth.set_authentication_headers(auth_object, custom_headers=custom_headers)
    resp = requests.request(method, uri, headers=request_headers, **kwargs)
    if raise_exception:
        resp.raise_for_status()
    return resp


def delete(uri, auth_object, headers=None, verify=VERIFY_SSL, **kwargs):
    resp = request("delete", uri, auth_object, headers=headers, verify=verify, **kwargs)
    return resp


def get(uri, auth_object, params=None, headers=None, verify=VERIFY_SSL, **kwargs):
    resp = request("get", uri, auth_object, params=params, headers=headers, verify=verify, **kwargs)
    return resp


def head(uri, auth_object, headers=None, verify=VERIFY_SSL, **kwargs):
    kwargs.setdefault("allow_redirects", False)
    resp = request("head", uri, auth_object, headers=headers, verify=verify, **kwargs)
    return resp


def options(uri, auth_object, headers=None, verify=VERIFY_SSL, **kwargs):
    resp = request("options", uri, auth_object, headers=headers, verify=verify, **kwargs)
    return resp


def patch(uri, auth_object, data=None, headers=None, verify=VERIFY_SSL, **kwargs):
    resp = request("patch", uri, auth_object, data=data, headers=headers, verify=verify, **kwargs)
    return resp


def post(uri, auth_object, data=None, json=None, headers=None, verify=VERIFY_SSL, **kwargs):
    resp = request("post", uri, auth_object, data=data, json=json, headers=headers, verify=verify, **kwargs)
    return resp


def put(uri, auth_object, data=None, headers=None, verify=VERIFY_SSL, **kwargs):
    resp = request("put", uri, auth_object, data=data, headers=headers, verify=verify, **kwargs)
    return resp
