FILTER_PATH_SEPARATOR = "."
FILTER_PATH_INVERSION = "^"


class PathElement:
    """Helper class for handling paths with optional semantic prefixes, in the following order:

    - inversion marked by a leading '^'.
    - count marked by a trailing '#'
    - distinct marked by a trailing '!'

    Can be used for any string, not just RDF predicates."""

    def __init__(self, entity: str = ""):
        self.inverted = entity.startswith("^")
        self.entity = entity[1 if self.inverted else 0 :]
        self.distinct = self.entity.endswith("!")
        self.entity = self.entity[: -1 if self.distinct else None]
        self.count = self.entity.endswith("#")
        self.entity = self.entity[: -1 if self.count else None]

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.entity == other.entity
            and self.inverted == other.inverted
        )

    def __hash__(self):
        return self.__str__().__hash__()

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


def parse_endpointspec(pathid_endpointname: str) -> tuple[str, str, dict]:
    """Return the WissKI path id, endpoint URL and orderable fields from an endpoint
    spec string, e.g.: 'person' -> ('person', '/person', {})
    'person/myendpoint/list?sort1|f1,f2' -> ('person', '/myendpoint/list', { 'orderable': ['sort1'], 'filterable': ['f1, f2']})
    """

    filterable = []
    if "|" in pathid_endpointname:
        pathid_endpointname, filterable = pathid_endpointname.split("|", 1)
        filterable = filterable.split(",")

    orderable = []
    if "?" in pathid_endpointname:
        pathid_endpointname, orderable = pathid_endpointname.split("?", 1)
        orderable = orderable.split(",")

    if "/" in pathid_endpointname:
        pathid_endpointname, endpoint_path = pathid_endpointname.split("/", 1)
    else:
        endpoint_path = pathid_endpointname
    return (
        pathid_endpointname,
        f"/{endpoint_path}",
        {
            "orderable": orderable,
            "filterable": filterable,
        },
    )


def parse_filterspec(filterspec: list[str]) -> dict[PathElement, list[str | None]]:
    """['a', 'b.c', 'd.e', 'd.f.g', 'h!.i'] -> {'a': [None], 'b': [['c']], 'd': [['e'], ['f.g']], 'h': [None, 'i']}"""
    split = [i.split(FILTER_PATH_SEPARATOR, 1) for i in filterspec]
    prefixes = set(p for p, *_ in split)
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
