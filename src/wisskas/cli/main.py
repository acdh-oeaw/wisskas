import argparse
import json
import logging
import pathlib
from typing import Callable

from rich_argparse import RichHelpFormatter

from wisskas.cli.endpoints import register_subcommand as endpoints_args
from wisskas.cli.filter import register_subcommand as filter_args
from wisskas.cli.paths import register_subcommand as paths_args


def main(args=None):
    parser = argparse.ArgumentParser(formatter_class=RichHelpFormatter)
    parser.add_argument(
        "-input",
        type=pathlib.Path,
        default="tests/data/releven_assertions_20240821.xml",
        help="a WissKI pathbuilder file",
    )

    subparsers = parser.add_subparsers(
        title="CLI commands",
        required=True,
    )

    def add_command(command: str, add_subcommand_args: Callable, **kwargs):
        subparser = subparsers.add_parser(
            command,
            formatter_class=RichHelpFormatter,
            **kwargs,
        )
        command_main = add_subcommand_args(subparser)
        # TODO check if a callable was returned
        subparser.set_defaults(func=command_main)

        return subparser

    add_command(
        "endpoints",
        endpoints_args,
        help="generate models, queries and FastAPI endpoints to be used with rdfproxy",
    )
    add_command("filter", filter_args, help="create a filtered pathbuilder file")
    add_command("paths", paths_args, help="inspect pathbuilder definitions")

    cli_output = parser.add_argument_group(
        "CLI options",
    )
    cli_output.add_argument(
        "--color-theme",
        default="dracula",
        help="color scheme to use for console output syntax highlighting (see https://pygments.org/docs/styles/#getting-a-list-of-available-styles)",
    )

    cli_output.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase the verbosity of the logging output: default is WARNING, use -v for INFO, -vv for DEBUG",
    )

    args = parser.parse_args(args)

    logging.basicConfig(
        level=max(10, 30 - 10 * args.verbose),
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.input.suffix == ".json":
        with open(args.input) as j:
            xml = json.load(j)["xml"]
            args.input = args.input.with_suffix(".xml")
            # exclusive creation
            # TODO print informative message if file already exists
            with open(args.input, "x") as x:
                x.write(xml)

    # call subcommand
    args.func(args)
