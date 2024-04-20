from pydantic import BaseModel, Extra

class Quote:
    pass

class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""



