import json
from tabulate import tabulate


class PermissionsSerializer:

    @staticmethod
    def serialize_details(resp, format, showindex=False, tablefmt="plain"):
        if format == "text":
            return resp.text

        data = resp.json().get("resourcePermission", [])

        if format == "json":
            return data

        if format == "table":
            rows = [[r["organization"], r["path"], r["permissions"]] for r in data]

            headers = (["id", "organization", "path", "permissions"] if showindex else ["organization", "path", "permissions"])

            return tabulate(rows, headers=headers, showindex=showindex, tablefmt=tablefmt)

        return resp
