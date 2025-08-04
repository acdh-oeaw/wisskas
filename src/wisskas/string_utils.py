FILTER_PATH_SEPARATOR = "."
FILTER_PATH_INVERSION = "^"


class PathElement:
    """Helper class for handling inversions marked by a leading '^'.

    Can be used for any string, not just RDF predicates."""

    def __init__(self, entity: str):
        self.inverted = entity.startswith("^")
        self.entity = entity[1 if self.inverted else 0 :]

    def __repr__(self):
        return f"PathElement('{str(self)}')"

    def __str__(self):
        return ("^" if self.inverted else "") + self.entity


def create_names(
    prefix: str | list[str], postfix: str, used_names=set(), n=1
) -> list[str]:
    # TODO check if already in used_names
    return (
        []
        if n == 0
        else [*(f"{prefix}_{i}_{postfix}" for i in range(n - 1)), f"{prefix}_{postfix}"]
    )


def to_classname(text: str) -> str:
    """Generate a valid Python class name from a string"""
    return text.replace("_", " ").title().replace(" ", "")


def to_fieldname(text: str) -> str:
    """Generate a valid Python field name from a string"""
    return text.replace("/", "").replace(" ", "_")


def parse_endpointspec(pathid_endpointname: str) -> tuple[str, str, list[str]]:
    """Return the WissKI path id, endpoint URL and orderable fields from an endpoint
    spec string, e.g.: 'person' -> ('person', '/person', [])
    'person/myendpoint/list?sort1' -> ('person', '/myendpoint/list', ['sort1'])
    """
    orderable = []

    if "?" in pathid_endpointname:
        pathid_endpointname, orderable = pathid_endpointname.split("?", 1)
        orderable = orderable.split(",")

    if "/" in pathid_endpointname:
        pathid_endpointname, endpoint_path = pathid_endpointname.split("/", 1)
    else:
        endpoint_path = pathid_endpointname
    return (pathid_endpointname, f"/{endpoint_path}", orderable)


def parse_filterspec(filterspec: list[str]) -> dict[PathElement, list[str]]:
    """['a', 'b.c', 'd.e', 'd.f.g'] -> {'a': [], 'b': [['c']], 'd': [['e'], ['f.g']]}"""
    split = [i.split(FILTER_PATH_SEPARATOR, 1) for i in filterspec]
    prefixes = set(p for p, *_ in split)
    # TODO handle * and ** here, or further up?
    return {
        PathElement(p): [r[1] for r in split if r[0] == p and len(r) > 1]
        for p in prefixes
    }


def path_to_camelcase(url_path) -> str:
    # or .title() on spaced string
    return "".join([s.capitalize() for s in split_url_path(url_path)])


def path_to_filename(url_path) -> str:
    return "_".join(split_url_path(url_path))


def split_url_path(url_path) -> list[str]:
    return url_path.lstrip("/").split("/")
