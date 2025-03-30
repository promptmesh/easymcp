from asyncio import Future, Queue

from mcp import types

from loguru import logger


class RequestMap:
    """RequestMap class"""

    requests: dict[str, Future[types.JSONRPCResponse | None]]

    outgoing_messages: Queue[types.JSONRPCMessage]

    def __init__(self, outgoing_messages: Queue[types.JSONRPCMessage]):
        self.outgoing_messages = outgoing_messages
        self.requests = {}

    def send_request(self, message: types.JSONRPCRequest):
        """send a request"""

        logger.debug(f"Sending request: {message}")

        future = Future[types.JSONRPCResponse | None]()

        self.requests[str(message.id)] = future

        wrapped_message = types.JSONRPCMessage(message)
        self.outgoing_messages.put_nowait(wrapped_message)
        return future

    def resolve_request(self, message: types.JSONRPCResponse):
        """resolve a request"""

        logger.debug(f"Resolving request: {message}")

        request_id = message.id
        future = self.requests.pop(str(request_id), None)
        if future is not None:
            future.set_result(message)

    def resolve_error(self, message: types.JSONRPCError):
        """resolve an error"""

        logger.debug(f"Resolving error: {message}")

        request_id = message.id
        future = self.requests.pop(str(request_id), None)
        if future is not None:
            future.set_result(None)