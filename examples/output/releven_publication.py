from typing import Annotated

from pydantic import AnyUrl, BaseModel
from rdfproxy import SPARQLBinding


class Publication_PublicationCreation(BaseModel):
    class Config:
        title = "Publication creation"
        model_bool = "publication__publication_creation"
    publication_creation_event: Annotated[AnyUrl | None, SPARQLBinding(
        "publication__publication_creation__publication_creation_event")]


class Publication(BaseModel):
    class Config:
        title = "Publication"
        model_bool = "publication"
        group_by = "publication"
    publication_reference: Annotated[str | None, SPARQLBinding(
        "publication__publication_reference")]
    publication_creation: Annotated[list[Publication_PublicationCreation], SPARQLBinding(
        "publication__publication_creation")]

