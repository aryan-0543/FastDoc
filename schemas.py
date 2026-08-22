from pydantic import BaseModel, ConfigDict, Field


class DocBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    category: str | None = None
    status: str | None = None


class DocCreate(DocBase):
    pass


class DocResponse(DocBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: str
