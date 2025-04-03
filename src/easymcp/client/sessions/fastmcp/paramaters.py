from pydantic import BaseModel

class FastMCPParamaters(BaseModel):
    module: str
    factory: bool = False