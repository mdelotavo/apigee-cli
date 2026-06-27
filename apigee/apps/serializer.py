import json


class AppsSerializer:

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