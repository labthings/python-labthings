from labthings.server.default_views.sockets import (
    socket_handler,
    process_socket_message,
)


def test_socket_handler(thing_ctx, fake_websocket):
    with thing_ctx.test_request_context():
        ws = fake_websocket("", recieve_once=True)
        socket_handler(ws)
        # Only responses should be announcing new subscribers
        for response in ws.responses:
            assert '"message": "Added subscriber' in response


### Will need regular updating as new message handlers are added
def test_process_socket_message():
    assert process_socket_message("message") is None
    assert process_socket_message(None) is None
