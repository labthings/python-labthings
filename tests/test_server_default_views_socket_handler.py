from labthings.server.default_views.sockets import socket_handler


def test_socket_handler(thing_ctx, fake_websocket):
    with thing_ctx.test_request_context():
        ws = fake_websocket("", recieve_once=True)
        socket_handler(ws)
        # Only responses should be announcing new subscribers
        for response in ws.responses:
            assert '"message": "Added subscriber' in response
