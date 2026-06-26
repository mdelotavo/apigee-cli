import json


class DevelopersSerializer:

    @staticmethod
    def serialize_details(resp, format, prefix=None):
        if format == "text":
            return resp.text

        data = resp.json()

        if prefix:
            data = [d for d in data if d.startswith(prefix)]

        if format == "dict":
            return data

        if format == "json":
            return json.dumps(data)

        return resp
