from asyncio import Future, Queue

import easymcp.vendored.types as types

class RequestMap:
    """RequestMap class"""

    requests: dict[str, Future[types.JSONRPCResponse]]
    
    outgoing_messages: Queue[types.JSONRPCMessage]

    def __init__(self, outgoing_messages: Queue[types.JSONRPCMessage]):
        self.outgoing_messages = outgoing_messages
        self.requests = {}

    def send_request(self, message: types.JSONRPCRequest):
        """send a request"""

        future = Future[types.JSONRPCResponse]()

        self.requests[str(message.id)] = future

        wrapped_message = types.JSONRPCMessage(message)
        self.outgoing_messages.put_nowait(wrapped_message)
        return future
    
    def resolve_request(self, message: types.JSONRPCResponse):
        """resolve a request"""
        request_id = message.id
        print(self.requests)
        future = self.requests.pop(str(request_id), None)
        if future is not None:
            future.set_result(message)