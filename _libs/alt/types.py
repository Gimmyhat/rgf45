from pydantic import BaseModel
import pprint


class Strict(BaseModel):
    class Config:
        extra = 'forbid'
        validate_assignment = True

    def __repr__(self):
        return pprint.pformat(self.dict(), sort_dicts=False)

    def __str__(self):
        return pprint.pformat(self.dict(), sort_dicts=False)
