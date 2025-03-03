from argparse import ArgumentParser
import logging
from typing import Callable

from lxml import etree
from rich import print
from rich.syntax import Syntax

from wisskas.wisski import parse_pathbuilder_paths

logger = logging.getLogger(__name__)


def register_subcommand(parser: ArgumentParser) -> Callable:
    parser.add_argument(
        "filter",
        metavar="field=value",
        nargs="+",
        help="something like 'id=person' or 'enabled=0'. put in same clause for AND, separate clauses for OR",
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs="?",
        help="output filename to write to. If none given, prints to stdout.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="check the resulting pathbuilder output is valid (by parsing it one more time)",
    )
    return main


def main(args):
    paths = parse_pathbuilder_paths(args.input, include_disabled=True)
    filters = [clause.split("=", 1) for clause in args.filter]
    # TODO check for invalid filter specs instead of letting it crash/fail silently?

    filtered_paths = []
    for path in paths.values():
        for clause in filters:
            if path.xml[clause[0]].text == clause[1]:
                logger.info(f"including path {path.id}")
                filtered_paths.append(path)
                break  # one level

    root = etree.Element("pathbuilderinterface")
    for path in filtered_paths:
        root.append(path.xml)

    if args.validate:
        logger.info(
            "validating filtered pathbuilder definition by running it through the parser:"
        )
        # emits logger messages if something is wrong
        parse_pathbuilder_paths(etree.tostring(root))

    if args.output:
        print(f"Writing {len(filtered_paths)} paths to {args.output}")
        etree.ElementTree(root).write(args.output, pretty_print=True)
    else:
        print(
            Syntax(
                etree.tostring(root, pretty_print=True, encoding="unicode"),
                "xml",
                theme=args.color_theme,
            )
        )
    logger.info(
        f"filtered pathbuilder definition from {len(paths)} to {len(filtered_paths)} paths"
    )
