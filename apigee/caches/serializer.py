import json


class CachesSerializer:

    @staticmethod
    def serialize_details(resp, format, prefix=None):
        if format == "text":
            return resp.text

        data = resp.json()

        if prefix:
            data = [c for c in data if c.startswith(prefix)]

        if format == "dict":
            return data

        if format == "json":
            return json.dumps(data)

        return resp