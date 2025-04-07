from pydantic import BaseModel

class FastMcpParameters(BaseModel):
    module: str
    factory: bool = False
    env: dict = {}
    argv: list = []