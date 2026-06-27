import json
from requests.exceptions import HTTPError

import apigee.request
from apigee import APIGEE_ADMIN_API_URL, console
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

    def create_api_product(self, body):
        return apigee.request.post(
          f"{APIGEE_ADMIN_API_URL}{CREATE_API_PRODUCT_PATH.format(org=self.org)}",
          self.auth,
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def delete_api_product(self):
        return apigee.request.delete(
          f"{APIGEE_ADMIN_API_URL}{DELETE_API_PRODUCT_PATH.format(org=self.org, name=self.name)}",
          self.auth,
        )

    def get_api_product(self):
        return apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{GET_API_PRODUCT_PATH.format(org=self.org, name=self.name)}",
          self.auth,
        )

    def update_api_product(self, body):
        return apigee.request.put(
          f"{APIGEE_ADMIN_API_URL}{UPDATE_API_PRODUCT_PATH.format(org=self.org, name=self.name)}",
          self.auth,
          json=json.loads(body),
          headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
        )

    def list_api_products(self, prefix=None, expand=False, count=1000, startkey="", format="json"):
        resp = apigee.request.get(
          f"{APIGEE_ADMIN_API_URL}{LIST_API_PRODUCTS_PATH.format(org=self.org)}",
          self.auth,
          params={
            "expand": expand,
            "count": count,
            "startKey": startkey,
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
