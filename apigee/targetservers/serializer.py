import json


class TargetserversSerializer:

    @staticmethod
    def serialize_details(resp, format, prefix=None):
        if format == "text":
            return resp.text

        data = resp.json()

        if prefix:
            data = [t for t in data if t.startswith(prefix)]

        if format == "dict":
            return data

        if format == "json":
            return json.dumps(data)

        return resp