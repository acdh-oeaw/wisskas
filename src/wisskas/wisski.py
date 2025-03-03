from collections.abc import Iterable
import logging
import pathlib

from lxml import etree, objectify

from wisskas.string_utils import PathElement, id_to_classname

logger = logging.getLogger(__name__)

WISSKI_TYPES = {
    # TODO add support for all Wisski field types: https://wiss-ki.eu/documentation/pathbuilder/configuration/lists
    "datetime": "datetime.datetime",
    "list_string": "list[str]",  # FIXME this doesn't get annotated properly, need to change the Type's cardinality instead
    "string": "str",
    "uri": "AnyUrl",
}


class WissKIPath:
    def __init__(self, path_element: etree._Element):
        if path_element.tag != "path":
            # TODO @lupl needs to create a schema for WissKI paths and validate against it
            raise ValueError("WissKIPath expects a <path> element")

        # raw data from WissKI XML
        self.xml = path_element

        # computed/derived fields
        self.cardinality = self.xml["cardinality"]
        self.path_array = [
            PathElement(el.text) for el in path_element.path_array.iterchildren()
        ]

        self.id = self.xml["id"].text
        self.fields = {}
        self.parents = {}
        self.binding_vars = []

        # TODO add to path instead?
        self.datatype_property = (
            self.xml["datatype_property"]
            if self.xml["datatype_property"] != "empty"
            else None
        )

        # set rdf class if this is a root type (== it has no parent group)
        self.rdf_class = self.last_entity() if self.xml["group_id"] == 0 else None
        self.group_id = self.xml["group_id"] if self.xml["group_id"] != 0 else None

        # is_group is misleading, paths are groups if their fields isn't empty
        self.class_name = id_to_classname(self.id) if self.xml["is_group"] else None

        self.entity_reference = self.xml["fieldtype"] == "entity_reference"

        # set python field type
        self.type = (
            WISSKI_TYPES[self.xml["fieldtype"]]
            if self.xml["fieldtype"] and not self.entity_reference
            else None
        )

    def last_entity(self) -> str:
        return self.path_array[-1].entity


WissKIPaths = dict[str, WissKIPath]


def root_type_dict(paths: Iterable[WissKIPath]) -> WissKIPaths:
    """Creates a dict which maps rdf class uris to WisskIPath types"""
    return {path.rdf_class: path for path in paths if path.rdf_class}


def parse_pathbuilder_paths(
    xml: pathlib.Path | str, include_disabled=False
) -> WissKIPaths:
    """Parses a pathbuilder XML definition from a file or XML string. Returns as a flat dict of WissKIPaths"""
    if isinstance(xml, pathlib.Path):
        root_element = objectify.parse(xml).getroot()
    else:
        root_element = objectify.fromstring(xml)

    return check_paths(
        {
            path_element["id"].text: WissKIPath(path_element)
            for path_element in root_element.iterchildren()
            if include_disabled or path_element.enabled
        }
    )


def check_paths(paths: WissKIPaths) -> WissKIPaths:
    """Check WissKI pathbuilder paths for consistency, emit logging messages and return them"""
    for path in paths.values():
        if path.group_id and path.group_id not in paths:
            logger.warning(
                f"path {path.id} is grouped under nonexisting parent path: {path.group_id}"
            )
    return paths


def nest_paths(
    paths: WissKIPaths,
) -> tuple[WissKIPaths, WissKIPaths]:
    """Adds field, parent and entity_references to a flat dict of paths"""
    root_types = root_type_dict(paths.values())

    # create nested structure
    for path in paths.values():
        if path.group_id:
            try:
                paths[path.group_id].fields[path.id] = path
                if path.entity_reference:
                    # look up based on CRM type
                    try:
                        path.entity_reference = root_types[path.last_entity()]
                        path.entity_reference.parents[path.id] = path
                        # path["fields"] = path["reference"]["fields"]
                        # path["is_group"] = 1
                    except KeyError as e:
                        logger.warning(
                            f"path '{path.id}' is an entity_reference, but no known path for target CRM class '{e}'"
                        )
                        path.entity_reference = False
            except KeyError:
                logger.error(
                    f"path '{path.id}' is grouped under path id '{path.group_id}' which is missing"
                )

    return (root_types, paths)


def parse_paths(xml: pathlib.Path | str) -> tuple[WissKIPaths, WissKIPaths]:
    """Return a tuple dicts, the first mapping RDF class names to WissKIPath, the second mapping WissKI path ids to WissKIPaths"""
    return nest_paths(parse_pathbuilder_paths(xml))
