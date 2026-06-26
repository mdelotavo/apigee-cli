import asyncio
from requests.exceptions import HTTPError

from apigee.apiproducts.apiproducts import Apiproducts
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class ApiProductsBackup(BaseBackup):

    async def snapshot(self):
        return await run_blocking(
          Apiproducts(self.config.authentication, self.config.org_name, None).list_api_products,
          self.config.prefix,
          "dict",
        )

    def save_snapshot(self, data):
        self.config.snapshot_data.apiproducts = data

        path = self.full_path("snapshots/apiproducts/apiproducts.json")
        write_content_to_file(data, path, indentation=2)

    async def download(self):
        tasks = [self._download(product) for product in self.config.snapshot_data.apiproducts]
        await asyncio.gather(*tasks)

    async def _download(self, apiproduct):
        try:
            content = await run_blocking(Apiproducts(self.config.authentication, self.config.org_name, apiproduct).get_api_product)

            path = self.full_path(f"apiproducts/{apiproduct}.json")

            await run_blocking(write_content_to_file, content.text, path, 2)

            self.progress("API Products")

        except HTTPError as e:
            self.handle_http_error(e, f" for API Product ({apiproduct})")
        except Exception as e:
            self.handle_error(e, apiproduct)
