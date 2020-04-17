
def test_docs(thing, thing_client, app_ctx):
    with thing_client as c:
        assert c.get("/docs/swagger").json == thing.spec.to_dict() 
        assert c.get("/docs/swagger-ui").status_code == 200