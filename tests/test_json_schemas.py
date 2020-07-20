from labthings.json import schemas


def make_rule(app, path, **kwargs):
    @app.route(path, **kwargs)
    def view():
        pass

    return app.url_map._rules_by_endpoint["view"][0]


def make_param(in_location="path", **kwargs):
    ret = {"in": in_location, "required": True}
    ret.update(kwargs)
    return ret


def test_rule_to_path(app):
    rule = make_rule(app, "/path/<id>/")
    assert schemas.rule_to_path(rule) == "/path/{id}/"


def test_rule_to_param(app):
    rule = make_rule(app, "/path/<id>/")
    assert schemas.rule_to_params(rule) == [
        {"in": "path", "name": "id", "required": True, "schema": {"type": "string"}}
    ]


def test_rule_to_param_typed(app):
    rule = make_rule(app, "/path/<int:id>/")
    assert schemas.rule_to_params(rule) == [
        {
            "in": "path",
            "name": "id",
            "required": True,
            "schema": {"type": "integer"},
            "format": "int32",
        }
    ]


def test_rule_to_param_typed_default(app):
    rule = make_rule(app, "/path/<int:id>/", defaults={"id": 1})
    assert schemas.rule_to_params(rule) == [
        {
            "in": "path",
            "name": "id",
            "required": True,
            "default": 1,
            "schema": {"type": "integer"},
            "format": "int32",
        }
    ]


def test_rule_to_param_overrides(app):
    rule = make_rule(app, "/path/<id>/")
    overrides = {"override_key": {"in": "header", "name": "header_param"}}
    assert schemas.rule_to_params(rule, overrides=overrides) == [
        {"in": "path", "name": "id", "required": True, "schema": {"type": "string"}},
        *overrides.values(),
    ]


def test_rule_to_param_overrides_invalid(app):
    rule = make_rule(app, "/path/<id>/")
    overrides = {"override_key": {"in": "invalid", "name": "header_param"}}
    assert schemas.rule_to_params(rule, overrides=overrides) == [
        {"in": "path", "name": "id", "required": True, "schema": {"type": "string"}}
    ]
