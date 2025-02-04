from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(loader=PackageLoader("wisskas"), autoescape=select_autoescape())

# add support for any/all filters
env.filters["any"] = any
env.filters["all"] = all


def serialize(template_name, **kwargs):
    template = env.get_template(f"{template_name}.jinja")
    return template.render(**kwargs)


def serialize_entrypoint(endpoints, backend_address, git_endpoint=False, cors={}):
    return serialize(
        "entrypoint.py",
        **{
            "backend_address": backend_address,
            "cors": cors,
            "endpoints": endpoints,
            "git": git_endpoint,
        },
    )


def serialize_model(root):
    return serialize("model.py", **{"root": root})


def serialize_query(root, prefixes={}):
    return serialize("query.rq", **{"root": root, "prefixes": prefixes})
