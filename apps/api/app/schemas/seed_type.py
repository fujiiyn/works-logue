import uuid

from pydantic import BaseModel


class SeedTypeResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str

    model_config = {"from_attributes": True}
