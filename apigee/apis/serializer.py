import json

from apigee.utils import remove_last_elements


class ApisSerializer:

    @staticmethod
    def filter_deployed_revisions(details):
        return list({rev["revision"] for env in details for rev in env.get("revision", [])})

    @staticmethod
    def filter_deployment_details(details):
        return [{
          "name": env["name"],
          "revision": [r["name"] for r in env.get("revision", [])],
        } for env in details.get("environment", [])]

    @staticmethod
    def filter_undeployed_revisions(all_revisions, deployed_revisions, save_last=0):
        deployed = set(deployed_revisions)
        undeployed = sorted(int(r) for r in all_revisions if r not in deployed)
        return remove_last_elements(undeployed, save_last)

    @staticmethod
    def serialize_details(resp, format, prefix=None):
        if format == "text":
            return resp.text

        data = resp.json()

        if prefix:
            data = [a for a in data if a.startswith(prefix)]

        if format == "dict":
            return data

        if format == "json":
            return json.dumps(data)

        return resp
