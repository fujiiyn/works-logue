import uuid

from pydantic import BaseModel


class TagResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str

    model_config = {"from_attributes": True}


class TagTreeNode(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    is_leaf: bool
    children: list["TagTreeNode"] = []

    model_config = {"from_attributes": True}
