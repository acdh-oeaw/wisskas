
from os import path
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from git import Repo
from rdfproxy import Page, QueryParameters, SPARQLModelAdapter
from releven_boulloterion import Boulloterion
from releven_external_authority import ExternalAuthority
from releven_person import Person
from releven_publication import Publication

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# The automatic health check endpoint is /. The return code has to be 200 or 30x.
@app.get("/")
def version():
    repo = Repo(search_parent_directories=True)
    return {"version": repo.git.describe(tags=True, dirty=True, always=True)}


class external_authorityQueryParameters(QueryParameters):
    pass


@app.get("/external_authority")
def external_authority(params: Annotated[external_authorityQueryParameters, Query()]) -> Page[ExternalAuthority]:
    adapter = SPARQLModelAdapter(
        target="https://graphdb.r11.eu/repositories/RELEVEN",
        query=open(
            f"{path.dirname(path.realpath(__file__))}/releven_external_authority.rq").read().replace('\n ', ' '),
        model=ExternalAuthority)
    return adapter.query(params)


class publicationQueryParameters(QueryParameters):
    pass


@app.get("/publication")
def publication(params: Annotated[publicationQueryParameters, Query()]) -> Page[Publication]:
    adapter = SPARQLModelAdapter(
        target="https://graphdb.r11.eu/repositories/RELEVEN",
        query=open(
            f"{path.dirname(path.realpath(__file__))}/releven_publication.rq").read().replace('\n ', ' '),
        model=Publication)
    return adapter.query(params)


class boulloterionQueryParameters(QueryParameters):
    pass


@app.get("/boulloterion")
def boulloterion(params: Annotated[boulloterionQueryParameters, Query()]) -> Page[Boulloterion]:
    adapter = SPARQLModelAdapter(
        target="https://graphdb.r11.eu/repositories/RELEVEN",
        query=open(
            f"{path.dirname(path.realpath(__file__))}/releven_boulloterion.rq").read().replace('\n ', ' '),
        model=Boulloterion)
    return adapter.query(params)


class personQueryParameters(QueryParameters):
    pass


@app.get("/person")
def person(params: Annotated[personQueryParameters, Query()]) -> Page[Person]:
    adapter = SPARQLModelAdapter(
        target="https://graphdb.r11.eu/repositories/RELEVEN",
        query=open(
            f"{path.dirname(path.realpath(__file__))}/releven_person.rq").read().replace('\n ', ' '),
        model=Person)
    return adapter.query(params)

