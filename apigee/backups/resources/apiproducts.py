import asyncio
from requests.exceptions import HTTPError

from apigee import console
from apigee.apiproducts.apiproducts import Apiproducts
from apigee.utils import write_content_to_file

from ..base import BaseBackup
from ..utils import run_blocking


class ApiProductsBackup(BaseBackup):

    async def snapshot(self):
        client = Apiproducts(self.config.authentication, self.config.org_name, None)

        return await run_blocking(
          client.list_api_products,
          self.config.prefix,
          False,
          1000,
          "",
          "dict",
        )

    def save_snapshot(self, data):
        self.config.snapshot_data.apiproducts = data

        path = self.full_path("snapshots/apiproducts/apiproducts.json")
        write_content_to_file(data, path, indentation=2)

    async def download(self):
        tasks = []
        total = len(self.config.snapshot_data.apiproducts)

        console.echo(f"  Total apiproducts to download: {total}")

        self.config.total_items = getattr(self.config, "total_items", 0) + total

        for product in self.config.snapshot_data.apiproducts:
            tasks.append(asyncio.create_task(self._download(product)))

        await asyncio.gather(*tasks)

    async def _download(self, apiproduct):
        try:
            client = Apiproducts(self.config.authentication, self.config.org_name, apiproduct)

            resp = await run_blocking(client.get_api_product, )

            path = self.full_path(f"apiproducts/{apiproduct}.json")

            await run_blocking(write_content_to_file, resp.text, path, 2)

            self.progress("ApiProducts")

        except HTTPError as e:
            if e.response.status_code == 404:
                self.handle_http_error(e, f" for API Product ({apiproduct})")
                return
            raise

        except Exception as e:
            self.handle_error(e, apiproduct)
