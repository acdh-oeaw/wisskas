import logging
from argparse import ArgumentParser
from typing import Callable
from rich import print as rprint
from rich.rule import Rule
from rich.syntax import Syntax

from wisskas.filter import endpoint_exclude_fields, endpoint_include_fields
from wisskas.serialize import serialize_entrypoint, serialize_model, serialize_query
from wisskas.string_utils import parse_endpointspec, path_to_camelcase, path_to_filename
from wisskas.wisski import parse_paths

logger = logging.getLogger(__name__)


def register_subcommand(parser: ArgumentParser) -> Callable:
    parser.add_argument(
        "-p",
        "--prefix",
        nargs=2,
        metavar=("prefix", "full_url"),
        action="append",
        help="namespace replacements to carry out, use a --prefix for every prefix specification (default: %(default)s)",
        default=[],
    )

    parser.add_argument(
        "-0",
        "--everything-optional",
        action="store_true",
        help="also make fields with cardinality 1 optional (default: %(default)s)",
        default=False,
    )

    parser.add_argument(
        "-s",
        "--page-size",
        type=int,
        help="default page size to use for listing endpoints (default: %(default)s)",
        default=20,
    )

    parser.add_argument(
        "-le",
        "--listing-exclude-fields",
        nargs="+",
        metavar=("path_id[/endpoint/target/path]", "exclude_field"),
        action="append",
        help="a path id for which to generate a list/page endpoint, followed by 0 or more field paths that should be excluded from the endpoint return value. any fields not in this list will be included by default.",
        default=[],
    )

    parser.add_argument(
        "-ie",
        "--item-exclude-fields",
        nargs="+",
        metavar=("path_id[/endpoint/target/path]", "exclude_field"),
        action="append",
        help="a path id for which to generate an item/detail endpoint, the name of the model field to filter for, followed by 0 or more field paths that should be excluded from the endpoint return value. any fields not in this list will be included by default.",
        default=[],
    )

    parser.add_argument(
        "-li",
        "--listing-include-fields",
        nargs="+",
        metavar=("path_id[/endpoint/target/path]", "include_field"),
        action="append",
        help="a path id for which to generate a list/page endpoint, followed by 1 or more field paths that should be included in the endpoint return value.",
        default=[],
    )

    parser.add_argument(
        "-ii",
        "--item-include-fields",
        nargs="+",
        metavar=("path_id[/endpoint/target/path]", "include_field"),
        action="append",
        help="a path id for which to generate a item/detail endpoint, the name of the model field to filter for, followed by 1 or more field paths that should be included in the endpoint return value.",
        default=[],
    )

    parser.add_argument(
        "-mi",
        "--manual-item",
        nargs="+",
        metavar=('"/pathname" ModelName id_field modelfile.py queryfile.rq'),
        action="append",
        help="add an item endpoint for an externally defined model/query to the entrypoint",
        default=[],
    )

    parser.add_argument(
        "-ml",
        "--manual-listing",
        nargs="+",
        metavar=('"/pathname" ModelName modelfile.py queryfile.rq'),
        action="append",
        help="add a listing endpoint for an externally defined model/query to the entrypoint",
        default=[],
    )

    file_output = parser.add_argument_group(
        "File output options",
    )
    file_output.add_argument(
        "-o",
        "--output-prefix",
        help="write generated models and queries to disk, using this output filename prefix",
    )

    file_output.add_argument(
        "-a",
        "--server-address",
        metavar="sparql_api_url",
        help="also generate FastAPI routes for all endpoints at the --output-prefix location, pointing to the given SPARQL endpoint URL",
    )

    file_output.add_argument(
        "-c",
        "--counts-endpoint",
        action="store_true",
        help="generate a /counts endpoint that returns the result count of all generated endpoints",
    )

    file_output.add_argument(
        "--cors",
        nargs="*",
        default=["*"],
        help="allow CORS requests from these origins (default: %(default)s)",
    )

    file_output.add_argument(
        "--git-endpoint",
        action="store_true",
        help="whether to generate a git health check endpoint at '/'",
    )

    return main


def main(args):
    _root_types, paths = parse_paths(args.input)
    args.prefix = dict(args.prefix)
    endpoints = {}

    def add_endpoint(endpoint_path, endpoint):
        if endpoint_path in endpoints:
            raise RuntimeError(
                f"Endpoint path {endpoint_path} is specified more than once"
            )
        endpoints[endpoint_path] = endpoint

    for path_id, *filters in args.listing_include_fields:
        if len(filters) == 0:
            raise Exception(
                f"endpoint '{path_id}' is defined using --listing-include-fields but is missing any fields to include"
            )
        path_id, endpoint_path = parse_endpointspec(path_id)

        add_endpoint(
            endpoint_path,
            endpoint_include_fields(
                paths[path_id], filters, path_to_camelcase(endpoint_path)
            ),
        )

    for path_id, key_field, *filters in args.item_include_fields:
        if len(filters) == 0:
            raise Exception(
                f"endpoint '{path_id}' is defined using --item-include-fields but is missing any fields to include"
            )
        path_id, endpoint_path = parse_endpointspec(path_id)

        add_endpoint(
            endpoint_path,
            endpoint_include_fields(
                paths[path_id], filters, path_to_camelcase(endpoint_path)
            ),
        )
        endpoints[endpoint_path].key_field = key_field

    for path_id, *filters in args.listing_exclude_fields:
        path_id, endpoint_path = parse_endpointspec(path_id)

        add_endpoint(
            endpoint_path,
            endpoint_exclude_fields(
                paths[path_id],
                filters,
                path_to_camelcase(endpoint_path),
            ),
        )

    for path_id, key_field, *filters in args.item_exclude_fields:
        path_id, endpoint_path = parse_endpointspec(path_id)

        add_endpoint(
            endpoint_path,
            endpoint_exclude_fields(
                paths[path_id],
                filters,
                path_to_camelcase(endpoint_path),
            ),
        )
        endpoints[endpoint_path].key_field = key_field

    def print_code(code, language="python"):
        rprint(Syntax(code, language, theme=args.color_theme), "\n")

    def dump_to_file(content, filename):
        logger.info(f"writing '{filename}'")
        with open(filename, "w") as f:
            f.write(content)

    for path, root in endpoints.items():
        filename = f"{args.output_prefix or ''}_{path_to_filename(path)}"

        # this is the local filename
        root.filename = filename.rsplit("/", 1)[-1]
        if hasattr(root, "key_field"):
            root.item_key = root.key_field
        root.everything_optional = args.everything_optional

        model = serialize_model(root)
        query = serialize_query(root, args.prefix)

        if args.output_prefix:
            dump_to_file(model, f"{filename}.py")
            dump_to_file(query, f"{filename}.rq")

        else:
            rprint(Rule(path))
            print_code(model)
            print_code(query, "sparql")

    for path, modelname, id_field, modelfile, queryfile in args.manual_item:
        # TODO implement
        add_endpoint(path, None)
        # TODO add key_field = id_field

    for path, modelname, modelfile, queryfile in args.manual_listing:
        # TODO implement
        add_endpoint(path, None)

    entrypoint = serialize_entrypoint(
        endpoints,
        args.server_address,
        args.git_endpoint,
        args.counts_endpoint,
        {"origins": args.cors},
        args.page_size,
    )

    if args.server_address:
        if args.output_prefix:
            dump_to_file(entrypoint, f"{args.output_prefix}.py")
        else:
            rprint(Rule("FastAPI entry point"))
            print_code(entrypoint)
