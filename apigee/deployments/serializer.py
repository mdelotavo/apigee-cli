import json

from tabulate import tabulate


class DeploymentsSerializer:

    @staticmethod
    def serialize_details(resp, format, showindex=False, tablefmt="plain"):
        if format == "text":
            return resp.text

        data = resp.json().get("environment", [])

        rows = [[
          env["name"],
          [r["name"] for r in env.get("revision", [])],
          [r["state"] for r in env.get("revision", [])],
        ] for env in data]

        if format == "json":
            return json.dumps([{"name": r[0], "revision": r[1], "state": r[2]} for r in rows])

        if format == "table":
            headers = ["id", "name", "revision", "state"] if showindex else ["name", "revision", "state"]
            return tabulate(rows, headers=headers, showindex=showindex, tablefmt=tablefmt)

        raise ValueError(format)
