import copy
import logging

from wisskas.string_utils import (
    FILTER_PATH_SEPARATOR,
    PathElement,
    create_names,
    parse_filterspec,
)
from wisskas.wisski import WISSKI_TYPES, WissKIPath

logger = logging.getLogger(__name__)


class DummyRootPath(WissKIPath):
    def __init__(
        self,
        root_classname,
        root=None,
    ):
        self.path_array = []
        self.binding_vars = []
        self.fields = {root_classname: root}
        self.class_name = root_classname


def endpoint_exclude_fields(
    root,
    exclude,
    root_classname,
):
    return clone_exclude(
        DummyRootPath(
            root_classname,
            root,
        ),
        root_classname,
        exclude,
    )


def endpoint_include_fields(
    root,
    include,
    root_classname,
):
    return clone_include(
        DummyRootPath(
            root_classname,
            root,
        ),
        root_classname,
        include,
    )


def handle_recursion(prefix):
    # TODO try to find recursion pattern === identical adjacent sequences of path ids
    raise RuntimeError("recursion somewhere")


def debug(task, path, msg, depth):
    logger.debug(f"{' ' * 2 * depth}{task} '{path.id}': {msg}")


def debug_clone(path, msg, depth=0):
    debug("cloning", path, msg, depth)


def debug_filter(path, msg, depth=0):
    debug("filtering", path, msg, depth)


def create_clone(
    parent: WissKIPath,
    fieldname: str,
    filterspec: list[str],
    prefix,
    used_names,
    depth=0,
    resolve_entity_references=True,
) -> tuple[WissKIPath, dict[PathElement, list[str]]]:
    # shallow copy
    clone = copy.copy(parent.fields[fieldname])
    clone.path_array = copy.copy(clone.path_array)

    if parent.path_array == []:
        debug_clone(
            clone,
            f"root type, changing classname from {clone.class_name} to {fieldname}",
        )
        clone.class_name = fieldname
        clone.root = True

    varnames = copy.copy(parent.binding_vars) if parent.binding_vars else [fieldname]

    if clone.entity_reference and resolve_entity_references:
        debug_clone(clone, f"entity reference to '{clone.entity_reference.id}'", depth)
        clone.fields = clone.entity_reference.fields
        clone.class_name = f"{parent.class_name}_{clone.entity_reference.class_name}"
        clone.id = clone.entity_reference.id
    # set parent paths to None
    if len(clone.path_array) > len(parent.path_array):
        for i in range(len(parent.path_array)):
            if (
                parent.path_array[i] is None
                or clone.path_array[i] == parent.path_array[i]
            ):
                debug_clone(
                    clone,
                    f"ignoring prefix because it exists in parent '{parent.id}'",
                    depth,
                )
                clone.path_array[i] = None
            else:
                break
    else:
        # child of an entity_reference
        varnames = [parent.binding_vars[-1]]
        clone.path_array[0] = None

    if clone.datatype_property:
        debug_clone(clone, f"adding datatype_property to {clone.path_array}")
        clone.path_array.append(clone.datatype_property)

    if parent.binding_vars:
        for name in create_names(
            varnames[-1] if varnames else "",
            clone.id,
            used_names,
            1 + len(clone.path_array) // 2 - len(varnames),
        ):
            varnames.append(name)

    clone.binding_vars = varnames
    clone.binding = varnames[-1]
    debug_clone(clone, f"path {clone.path_array}", depth)
    debug_clone(clone, f"binding vars {clone.binding_vars}", depth)

    # parse and validate the filterspec, does not actually apply it
    filters = (
        [] if isinstance(filterspec, PathElement) else parse_filterspec(filterspec)
    )
    for key in filters:
        if key.inverted:
            raise RuntimeError("not implemented yet")
        elif key.count:
            pass
        else:
            # TODO warn about invalid/redundant combinations
            if key.entity in ["*", "**", "%", "%%"]:
                if len(key.entity) == 1 and len(clone.fields) == 0:
                    logger.warning(
                        f"found '{key}' at {'.'.join(prefix[1:])} even though there are no fields"
                    )
                else:
                    debug_clone(clone, f"found field '{key}'", depth)
                continue
            exists = False
            for f in clone.fields.values():
                if f.id == key.entity:
                    debug_clone(clone, f"found field '{key}'", depth)
                    exists = True
                    break
            if not exists:
                logger.warning(
                    f"cloning '{clone.id}': unknown field specified in include/exclude list at {FILTER_PATH_SEPARATOR.join(prefix[1:] or ['the top level'])}: '{key}'"
                )
    return (clone, filters)


def clone_exclude(
    parent: WissKIPath,
    fieldname: str,
    exclude,
    prefix=[],
    used_names=dict(),
    depth=0,
    resolve_entity_references=True,
) -> WissKIPath:
    clone, excludes = create_clone(
        parent,
        fieldname,
        exclude,
        prefix,
        used_names,
        depth,
        resolve_entity_references,
    )
    debug_filter(clone, f"raw exclude {exclude}")
    debug_filter(clone, f"parsed excludes {excludes}")
    if any(key.inverted for key in excludes):
        raise RuntimeError(
            f"path inversion only makes sense for including fields, not for excluding them (at '{prefix}')"
        )
    if "*" in exclude:
        clone.type = WISSKI_TYPES["uri"]
        clone.fields = {}
        # clone.datatype_property = None
        return clone

    if "%" in exclude:
        resolve_entity_references = False

    excludes = {a.entity: b for a, b in excludes.items()}

    try:
        clone.fields = {
            name: clone_exclude(
                clone,
                name,
                excludes.get(f.id, []),
                prefix,
                used_names,
                depth + 1,
                resolve_entity_references,
            )
            for name, f in clone.fields.items()
            if excludes.get(f.id, None) != []
        }
    except RecursionError:
        handle_recursion(prefix)
    return clone


def clone_include(
    parent: WissKIPath,
    fieldname: str,
    include,
    prefix=[],
    used_names=dict(),
    depth=0,
    resolve_entity_references=True,
) -> WissKIPath:
    clone, includes = create_clone(
        parent, fieldname, include, prefix, used_names, depth, resolve_entity_references
    )
    debug_filter(clone, f"raw include {include}", depth)
    debug_filter(clone, f"parsed includes {includes}", depth)
    if isinstance(include, PathElement):
        clone.fields = {}
        clone.distinct = include.distinct
        if include.count:
            clone.count = include.count
            clone.cardinality = 1
            clone.type = "int"
    elif "**" in include or "%%" in include:
        clone.fields = {
            name: clone_include(
                clone,
                name,
                ["**"],
                prefix,
                used_names,
                depth + 1,
                resolve_entity_references and "**" in include,
            )
            for name in clone.fields
        }
    else:
        # TODO handle inverted paths
        includes = {
            a.entity: a if a.count or a.distinct else b for a, b in includes.items()
        }
        clone.fields = {
            name: clone_include(
                clone,
                name,
                includes.get(name, []),
                prefix,
                used_names,
                depth + 1,
                resolve_entity_references and "%" not in include,
            )
            for name in clone.fields
            if "*" in include or "%" in include or name in includes
        }
    if len(clone.fields) == 0 and not clone.datatype_property and not clone.type:
        debug_filter(clone, "class is down to 0 fields", depth)
        clone.type = WISSKI_TYPES["uri"]
    else:
        debug_filter(clone, f"remaining fields {list(clone.fields.keys())}", depth)
    return clone
