import argparse
import logging

from wisskas.filter import clone_exclude, clone_include
from wisskas.serialize import (
    serialize,
    serialize_entrypoint,
    serialize_model,
    serialize_query,
)
from wisskas.string_utils import parse_endpointspec, path_to_camelcase
from wisskas.wisski import parse_paths

parser = argparse.ArgumentParser()
parser.add_argument(
    "--input",
    type=argparse.FileType("r"),
    default="releven_assertions_20240821.xml",
    help="a WissKI pathbuilder file",
)
parser.add_argument("--output", type=str, help="output filename")

endpoint_parser = parser.add_argument_group(
    "Endpoint/model options",
    "specify one or more WissKI path ids for which to generate endpoints (i.e. models + a query).\nIf no endpoints are given, lists all available types without generating any endpoints.",
)

endpoint_parser.add_argument(
    "-p",
    "--prefix",
    nargs=2,
    metavar=("prefix", "full_url"),
    action="append",
    help="namespace replacements to carry out, use a --prefix for every prefix specification (default: %(default)s)",
    default=[
        ["crm", "http://www.cidoc-crm.org/cidoc-crm/"],
        ["lrmoo", "http://iflastandards.info/ns/lrm/lrmoo/"],
        ["star", "https://r11.eu/ns/star/"],
        ["skos", "http://www.w3.org/2004/02/skos/core#"],
        ["r11", "https://r11.eu/ns/spec/"],
        ["r11pros", "https://r11.eu/ns/prosopography/"],
    ],
)

endpoint_parser.add_argument(
    "-ee",
    "--endpoint-exclude-fields",
    nargs="+",
    metavar=("path_id[/endpoint/target/path]", "exclude_field"),
    action="append",
    help="a path id for which to generate an endpoint, followed by 0 or more field paths that should be excluded from the endpoint return value. any fields not in this list will be included by default.",
    default=[
        [
            "publication/pub/list",
            "publication_text_assertion",
            "publication_creation.publication_creation_event.*",
        ]
    ],
)

endpoint_parser.add_argument(
    "-ei",
    "--endpoint-include-fields",
    nargs="+",
    metavar=("path_id[/endpoint/target/path]", "include_field"),
    action="append",
    help="a path id for which to generate an endpoint, followed by 1 or more field paths that should be included in the endpoint return value.",
    default=[],
)

parser.add_argument(
    "--cors",
    nargs="*",
    default=["*"],
    help="allow CORS requests from these origins (default: %(default)s)",
)

parser.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="Increase the verbosity of the logging output: default is WARNING, use -v for INFO, -vv for DEBUG",
)

args = parser.parse_args()
args.prefix = dict(args.prefix)

logging.basicConfig(
    level=max(10, 30 - 10 * args.verbose), format="%(levelname)s: %(message)s"
)

root_types, paths = parse_paths(args.input)

endpoints = {}

for path_id, *filters in args.endpoint_include_fields:
    if len(filters) == 0:
        raise Exception(
            f"endpoint '{path_id}' is defined using --endpoint-include-fields but is missing any fields to include"
        )
    path_id, endpoint_path = parse_endpointspec(path_id)

    if endpoint_path in endpoints:
        raise RuntimeError(f"Endpoint path {endpoint_path} is specified more than once")
    endpoints[endpoint_path] = clone_include(
        paths[path_id], filters, [path_to_camelcase(endpoint_path)]
    )

for path_id, *filters in args.endpoint_exclude_fields:
    path_id, endpoint_path = parse_endpointspec(path_id)

    if endpoint_path in endpoints:
        raise RuntimeError(f"Endpoint path {endpoint_path} is specified more than once")
    endpoints[endpoint_path] = clone_exclude(
        paths[path_id], filters, [path_to_camelcase(endpoint_path)]
    )

if len(endpoints) == 0:
    print(serialize("pathinfo", paths=paths))

else:
    for path in endpoints.values():
        model = serialize_model(path)
        query = serialize_query(path)
        entrypoint = serialize_entrypoint(endpoints, {"origins": args.cors})

        if args.output:
            # TODO write to file(s)
            pass

        else:
            print(model)
            print(query)
            print(entrypoint)
