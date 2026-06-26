import json
import requests
from requests.exceptions import HTTPError

from apigee import APIGEE_ADMIN_API_URL, auth, console
from apigee.apiproducts.serializer import ApiproductsSerializer
from apigee.utils import read_file_content

CREATE_API_PRODUCT_PATH = "/v1/organizations/{org}/apiproducts"
DELETE_API_PRODUCT_PATH = "/v1/organizations/{org}/apiproducts/{name}"
GET_API_PRODUCT_PATH = "/v1/organizations/{org}/apiproducts/{name}"
LIST_API_PRODUCTS_PATH = "/v1/organizations/{org}/apiproducts"
UPDATE_API_PRODUCT_PATH = "/v1/organizations/{org}/apiproducts/{name}"


class Apiproducts:

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
        resp = requests.request(method, url, headers=self._headers(kwargs.pop("headers", None)), **kwargs)
        resp.raise_for_status()
        return resp

    def create_api_product(self, body):
        payload = json.loads(body)
        return self._request(
          "post",
          CREATE_API_PRODUCT_PATH.format(org=self.org),
          headers={"Content-Type": "application/json"},
          json=payload,
        )

    def delete_api_product(self):
        return self._request(
          "delete",
          DELETE_API_PRODUCT_PATH.format(org=self.org, name=self.name),
        )

    def get_api_product(self):
        return self._request(
          "get",
          GET_API_PRODUCT_PATH.format(org=self.org, name=self.name),
        )

    def update_api_product(self, body):
        payload = json.loads(body)
        return self._request(
          "put",
          UPDATE_API_PRODUCT_PATH.format(org=self.org, name=self.name),
          headers={"Content-Type": "application/json"},
          json=payload,
        )

    def list_api_products(self, prefix=None, expand=False, count=1000, startkey="", format="json"):
        resp = self._request(
          "get",
          LIST_API_PRODUCTS_PATH.format(org=self.org),
          params={
            "expand": expand,
            "count": count,
            "startKey": startkey
          },
        )
        return ApiproductsSerializer().serialize_details(resp, format, prefix=prefix)

    def push_apiproducts(self, file):
        data = read_file_content(file, type="json")
        self.name = data["name"]

        try:
            self.get_api_product()
            console.echo(f"Updating {self.name}")
            console.echo(self.update_api_product(json.dumps(data)).text)
        except HTTPError as e:
            if e.response.status_code != 404:
                raise
            console.echo(f"Creating {self.name}")
            console.echo(self.create_api_product(json.dumps(data)).text)
