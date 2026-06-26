import requests

from apigee import APIGEE_ADMIN_API_URL, auth
from apigee.keystores.serializer import KeystoresSerializer

KEYSTORES_PATH = "/v1/o/{org}/environments/{env}/keystores"
KEYSTORE_PATH = "/v1/o/{org}/environments/{env}/keystores/{name}"
CERTS_PATH = "{base}/certs"
CERT_PATH = "{base}/certs/{cert}"
ALIASES_PATH = "{base}/aliases"
ALIAS_PATH = "{base}/aliases/{alias}"


class Keystores:

    def __init__(self, auth_config, org, name=None):
        self.auth = auth_config
        self.org = org
        self.name = name

    def _headers(self, extra=None):
        return auth.set_authentication_headers(
          self.auth,
          custom_headers={
            "Accept": "application/json",
            **(extra or {})
          },
        )

    def _request(self, method, path, **kwargs):
        url = f"{APIGEE_ADMIN_API_URL}{path}"
        resp = requests.request(
          method,
          url,
          headers=self._headers(kwargs.pop("headers", None)),
          **kwargs,
        )
        resp.raise_for_status()
        return resp

    def _base(self, env):
        return KEYSTORE_PATH.format(org=self.org, env=env, name=self.name)

    # --------------------
    # keystore
    # --------------------

    def get(self, env):
        return self._request("get", self._base(env))

    def list(self, env, prefix=None, format="json"):
        resp = self._request("get", KEYSTORES_PATH.format(org=self.org, env=env))
        return KeystoresSerializer().serialize_details(resp, format, prefix=prefix)

    # --------------------
    # certs
    # --------------------

    def list_certs(self, env, prefix=None, format="json"):
        resp = self._request("get", CERTS_PATH.format(base=self._base(env)))
        return KeystoresSerializer().serialize_details(resp, format, prefix=prefix)

    def get_cert(self, env, cert):
        return self._request("get", CERT_PATH.format(base=self._base(env), cert=cert))

    def export_cert(self, env, cert):
        return self._request("get", f"{CERT_PATH.format(base=self._base(env), cert=cert)}/export")

    # --------------------
    # aliases
    # --------------------

    def list_aliases(self, env, prefix=None, format="json"):
        resp = self._request("get", ALIASES_PATH.format(base=self._base(env)))
        return KeystoresSerializer().serialize_details(resp, format, prefix=prefix)

    def get_alias(self, env, alias):
        return self._request("get", ALIAS_PATH.format(base=self._base(env), alias=alias))

    def export_alias_cert(self, env, alias):
        return self._request(
          "get",
          f"{ALIAS_PATH.format(base=self._base(env), alias=alias)}/certificate",
        )
