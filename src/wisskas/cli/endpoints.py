from argparse import ArgumentParser
from typing import Callable
from rich import print as rprint
from rich.rule import Rule
from rich.syntax import Syntax

from wisskas.filter import endpoint_exclude_fields, endpoint_include_fields
from wisskas.serialize import serialize_entrypoint, serialize_model, serialize_query
from wisskas.string_utils import parse_endpointspec, path_to_camelcase, path_to_filename
from wisskas.wisski import parse_paths


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
        "-ee",
        "--endpoint-exclude-fields",
        nargs="+",
        metavar=("path_id[/endpoint/target/path]", "exclude_field"),
        action="append",
        help="a path id for which to generate an endpoint, followed by 0 or more field paths that should be excluded from the endpoint return value. any fields not in this list will be included by default.",
        default=[],
    )

    parser.add_argument(
        "-ei",
        "--endpoint-include-fields",
        nargs="+",
        metavar=("path_id[/endpoint/target/path]", "include_field"),
        action="append",
        help="a path id for which to generate an endpoint, followed by 1 or more field paths that should be included in the endpoint return value.",
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
        help="whether to generate a git health check endpoint a /",
    )

    return main


def main(args):
    _root_types, paths = parse_paths(args.input)
    args.prefix = dict(args.prefix)
    endpoints = {}

    for path_id, *filters in args.endpoint_include_fields:
        if len(filters) == 0:
            raise Exception(
                f"endpoint '{path_id}' is defined using --endpoint-include-fields but is missing any fields to include"
            )
        path_id, endpoint_path = parse_endpointspec(path_id)

        if endpoint_path in endpoints:
            raise RuntimeError(
                f"Endpoint path {endpoint_path} is specified more than once"
            )
        endpoints[endpoint_path] = endpoint_include_fields(
            paths[path_id], filters, path_to_camelcase(endpoint_path)
        )

    for path_id, *filters in args.endpoint_exclude_fields:
        path_id, endpoint_path = parse_endpointspec(path_id)

        if endpoint_path in endpoints:
            raise RuntimeError(
                f"Endpoint path {endpoint_path} is specified more than once"
            )
        endpoints[endpoint_path] = endpoint_exclude_fields(
            paths[path_id],
            filters,
            path_to_camelcase(endpoint_path),
        )

    def print_code(code, language="python"):
        rprint(Syntax(code, language, theme=args.color_theme), "\n")

    def dump_to_file(content, filename):
        print(f"writing {filename}")
        with open(filename, "w") as f:
            f.write(content)

    for path, root in endpoints.items():
        filename = f"{args.output_prefix or ''}_{path_to_filename(path)}"

        # this is the local filename
        root.filename = filename.rsplit("/", 1)[-1]
        root.details = path.endswith("details")
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

    entrypoint = serialize_entrypoint(
        endpoints,
        args.server_address,
        args.git_endpoint,
        args.counts_endpoint,
        {"origins": args.cors},
    )

    if args.server_address:
        if args.output_prefix:
            dump_to_file(entrypoint, f"{args.output_prefix}.py")
        else:
            rprint(Rule("FastAPI entry point"))
            print_code(entrypoint)
