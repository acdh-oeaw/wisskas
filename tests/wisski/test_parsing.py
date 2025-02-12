import pathlib
from wisskas.wisski import nest_paths, parse_pathbuilder_paths

test_data_file = pathlib.Path("tests/data/releven_assertions_20240821.xml")


def test_parse_pathbuilder_paths():
    # TODO test parsing from string
    # parse_pathbuilder_paths("<foo />")
    # test parsing from file
    parse_pathbuilder_paths(test_data_file)


def test_nest_paths():
    nest_paths(parse_pathbuilder_paths(test_data_file))
