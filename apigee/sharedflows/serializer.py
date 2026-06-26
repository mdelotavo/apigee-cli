import json

from apigee.utils import apply_function_on_iterable, remove_last_elements


class SharedflowsSerializer:

    @staticmethod
    def filter_deployed_revisions(details):
        return list(set(apply_function_on_iterable(details, lambda d: d["revision"], state_op="extend")))

    @staticmethod
    def filter_deployment_details(details):
        return apply_function_on_iterable(
          details.get("environment", []),
          lambda d: {
            "name": d["name"],
            "revision": [r["name"] for r in d.get("revision", [])],
          },
        )

    @staticmethod
    def filter_undeployed_revisions(revisions, deployed, save_last=0):
        undeployed = [int(r) for r in revisions if r not in deployed]
        return remove_last_elements(sorted(undeployed), save_last)

    @staticmethod
    def serialize_details(resp, format, prefix=None):
        if format == "text":
            return resp.text

        data = resp.json()

        if prefix:
            data = [s for s in data if s.startswith(prefix)]

        if format == "dict":
            return data

        if format == "json":
            return json.dumps(data)

        return resp
