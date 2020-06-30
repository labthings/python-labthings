from labthings.server.default_views.sockets import (
    socket_handler,
    process_socket_message,
)


def test_socket_handler(thing_ctx, fake_websocket):
    with thing_ctx.test_request_context():
        ws = fake_websocket("__unittest", recieve_once=True, close_after=["__unittest_response"])
        socket_handler(ws)
        assert "__unittest_response" in ws.responses


### Will need regular updating as new message handlers are added
def test_process_socket_message():
    assert process_socket_message("message") is None
    assert process_socket_message(None) is None
