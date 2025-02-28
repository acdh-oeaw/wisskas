from argparse import ArgumentParser
from typing import Callable

from rich import print as rprint
from rich.rule import Rule
from rich.tree import Tree

from wisskas.wisski import parse_pathbuilder_paths, parse_paths


def register_subcommand(parser: ArgumentParser) -> Callable:
    parser.set_defaults(func=main)
    parser.add_argument(
        "path_id", nargs="*", help="show path details for the given path id(s)."
    )
    parser.add_argument(
        "-a", "--all", action="store_true", help="show details of all available paths"
    )

    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument(
        "-f", "--flat", action="store_true", help="show flat (XML) path representation"
    )
    modes.add_argument(
        "-n", "--nested", action="store_true", help="show nested path representation"
    )
    return main


def main(args):
    def file_rule(msg):
        return Rule(f"{args.input.name}: {msg}")

    if args.flat:
        paths = parse_pathbuilder_paths(args.input)

        if args.all:
            args.path_id = sorted(paths.keys())

        if args.path_id:
            for path_id in args.path_id:
                rprint(paths[path_id].xml)
        else:
            for path in paths:
                rprint(f"- {path}")

        rprint(file_rule(f"{len(paths)} paths"))

    elif args.nested:
        root_types, paths = parse_paths(args.input)

        if args.all:
            args.path_id = sorted(path.id for path in root_types.values())

        if args.path_id:
            from pygments.styles import get_style_by_name
            from pygments.token import (
                Keyword,
                Comment,
                String,
                Literal,
                Number,
                Operator,
            )

            styles = get_style_by_name(args.color_theme).styles

            def generate_rich_tree(path, prefix=False):
                if path.entity_reference:
                    tp = f"[{styles[Keyword]}]{path.entity_reference.id}[default]/[{styles[Number]}]{path.path_array[-1]}"
                elif path.type:
                    tp = f"[{styles[String]}]{path.type}"
                elif prefix:
                    tp = f"[{styles[Comment]}]{path.path_array[-1]}"
                else:
                    tp = f"[{styles[Number]}]{path.path_array[-1]}"
                if prefix and path.cardinality == -1:
                    tp = f"list[ {tp} [default]]"
                tree = Tree(
                    f"[{styles[Operator]}][{styles[Literal]}]{path.id}[default]: {tp}[default]"
                )
                for field in path.fields.values():
                    tree.add(generate_rich_tree(field, True))

                return tree

            for path_id in args.path_id:
                if paths[path_id].rdf_class:
                    rprint(generate_rich_tree(paths[path_id]), "")
        else:
            for rdf_class, path in root_types.items():
                rprint(f"- {path.id}: {rdf_class}")
        rprint(
            Rule(f"{args.input.name}: {len(paths)} paths, {len(root_types)} root types")
        )
