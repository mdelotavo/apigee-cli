import apigee.request

from apigee import APIGEE_ADMIN_API_URL
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

    def _base(self, env):
        return KEYSTORE_PATH.format(org=self.org, env=env, name=self.name)

    # keystore

    def get(self, env):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{self._base(env)}",
          self.auth,
        )

    def list(self, env, prefix=None, format="json"):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{KEYSTORES_PATH.format(org=self.org, env=env)}",
          self.auth,
        )
        return KeystoresSerializer().serialize_details(resp, format, prefix=prefix)

    # certs

    def list_certs(self, env, prefix=None, format="json"):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{CERTS_PATH.format(base=self._base(env))}",
          self.auth,
        )
        return KeystoresSerializer().serialize_details(resp, format, prefix=prefix)

    def get_cert(self, env, cert):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{CERT_PATH.format(base=self._base(env), cert=cert)}",
          self.auth,
        )

    def export_cert(self, env, cert):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{CERT_PATH.format(base=self._base(env), cert=cert)}/export",
          self.auth,
        )

    # aliases

    def list_aliases(self, env, prefix=None, format="json"):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{ALIASES_PATH.format(base=self._base(env))}",
          self.auth,
        )
        return KeystoresSerializer().serialize_details(resp, format, prefix=prefix)

    def get_alias(self, env, alias):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{ALIAS_PATH.format(base=self._base(env), alias=alias)}",
          self.auth,
        )

    def export_alias_cert(self, env, alias):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{ALIAS_PATH.format(base=self._base(env), alias=alias)}/certificate",
          self.auth,
        )
