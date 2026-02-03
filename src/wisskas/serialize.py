from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(loader=PackageLoader("wisskas"), autoescape=select_autoescape())

# add support for any/all filters
env.filters["any"] = any
env.filters["all"] = all


def serialize(template_name: str, variables: dict):
    template = env.get_template(f"{template_name}.jinja")
    return template.render(variables)


def serialize_entrypoint(endpoints, backend_address: str, variables: dict) -> str:
    return serialize(
        "entrypoint.py",
        {  # defaults
            "cache": None,
            "cors": {},
            "counts_endpoint": False,
            "git_endpoint": False,
            "httpx_args": {},
            "httpx_transport_args": {},
            "logging": False,
            "page_size": None,
        }
        | variables
        | {
            "endpoints": endpoints,
            "backend_address": backend_address,
        },
    )


def serialize_model(root):
    return serialize("model.py", {"root": root})


def serialize_query(root, prefixes: dict[str, str] = {}):
    return serialize("query.rq", {"root": root, "prefixes": prefixes})
