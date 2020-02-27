from flask_restful import Resource, reqparse
from ... import r
from .. import auth


def tags_validator(tags):
    if isinstance(tags, dict):
        tags = [tags]
    if not isinstance(tags, list):
        raise ValueError("Tags field must be string or list")
    for tag in tags:
        if not isinstance(tag, dict):
            raise ValueError("One tag is not in dict format")
        if "name" not in tag or "value" not in tag:
            raise ValueError("Name and value fields must both exist in a tag dict")
    return tags


class Search(Resource):
    decorators = [auth.login_required]

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("building", type=str, required=True, location="json")
        parser.add_argument("tags", type=tags_validator, required=True, location="json")
        args = parser.parse_args()

        building = args["building"]
        tags = args["tags"]
        intersection = [
            "tag:{}:{}:{}".format(building, tag["name"], tag["value"]) for tag in tags
        ]
        return {"sensors": list(r.sinter(intersection))}
