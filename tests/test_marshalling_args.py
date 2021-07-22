from labthings import fields, views
from labthings.marshalling.args import use_args, use_body
from labthings.schema import Schema


def test_use_body_string(app, client):
    class Index(views.MethodView):
        @use_body(fields.String(required=True))
        def post(self, args):
            return args

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.post("/", data="string", content_type="application/json")
        assert res.data.decode() == "string"


def test_use_body_no_data_error(app, client):
    class Index(views.MethodView):
        @use_body(fields.String(required=True))
        def post(self, args):
            return args

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.post("/", content_type="application/json")
        assert res.status_code == 400


def test_use_body_no_data_missing(app, client):
    class Index(views.MethodView):
        @use_body(fields.String(missing="default"))
        def post(self, args):
            return args

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.post("/", content_type="application/json")
        assert res.data.decode() == "default"


def test_use_body_validation_error(app, client):
    class Index(views.MethodView):
        @use_body(fields.String(required=True))
        def post(self, args):
            return args

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.post("/", json={"foo": "bar"}, content_type="application/json")
        assert res.status_code == 400


def test_use_args_field(app, client):
    class Index(views.MethodView):
        @use_args(fields.String(required=True))
        def post(self, args):
            return args

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.post("/", data="string", content_type="application/json")
        assert res.data.decode() == "string"


def test_use_args_map(app, client):
    class Index(views.MethodView):
        @use_args({"foo": fields.String(required=True)})
        def post(self, args):
            return args

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.post("/", json={"foo": "bar"}, content_type="application/json")
        assert res.json == {"foo": "bar"}


def test_use_args_schema(app, client):
    class TestSchema(Schema):
        foo = fields.String(required=True)

    class Index(views.MethodView):
        @use_args(TestSchema())
        def post(self, args):
            return args

    app.add_url_rule("/", view_func=Index.as_view("index"))

    with client:
        res = client.post("/", json={"foo": "bar"}, content_type="application/json")
        assert res.json == {"foo": "bar"}
