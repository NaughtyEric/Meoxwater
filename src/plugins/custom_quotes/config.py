from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""
    quote_path: str

    def __init__(self, **data):
        super().__init__(**data)
        self.quote_path = self.quote_path.replace("\\", "/")
        if not self.quote_path.endswith("/"):
            self.quote_path += "/"



