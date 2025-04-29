from pydantic import BaseModel, Field, BaseConfig


class Config(BaseModel):
    """Plugin Config Here"""
    mngreeting_replies_filepath: str = "./assets/morning_night_greeting/replies.json"
    mngreeting_cooldown: int = 20
