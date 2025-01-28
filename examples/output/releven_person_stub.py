from pydantic import AnyUrl, BaseModel, Field  # noqa: F401
from rdfproxy import ConfigDict, SPARQLBinding
from typing import Annotated


class PersonStub(BaseModel):
    model_config = ConfigDict(
        title="Person",
        model_bool="id",
        group_by="id",
    )
    id: Annotated[AnyUrl | None, SPARQLBinding("Person_stub")] = Field(
        default=None, exclude=False
    )
    person_appellation_assertion: Annotated[
        list[AnyUrl], SPARQLBinding("Person_stub__person_appellation_assertion")
    ]
    person_descriptive_name: Annotated[
        list[str], SPARQLBinding("Person_stub__person_descriptive_name")
    ]
