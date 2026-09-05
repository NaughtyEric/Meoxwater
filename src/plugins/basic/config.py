from pydantic import BaseModel


class Config(BaseModel, extra="ignore"):
    """Plugin Config Here"""

    blocklist: list[str] = []
    admin: list[str] = []
