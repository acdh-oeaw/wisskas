# WissKAS `≡UωU≡`

![tests](https://github.com/acdh-oeaw/wisskas/actions/workflows/tests.yml/badge.svg)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

WissKI Adapter Serialization

## Rationale

WissKI pathbuilder defines (nested) models that are linked to RDF classes. By allowing fields to reference other pathbuilder models, it is possible to define recursive model structures. WissKAS provides:

- tools for parsing WissKI pathbuilder definitions (`wisskas.wisski`)
- tools for deriving limited depth submodels from those definitions (`wisskas.filter`)
- tools for generating [rdfproxy](https://github.com/acdh-oeaw/rdfproxy) endpoints from those models (`wisskas.serialize`)
- a command line tool for doing all of the above (`wisskas.cli`)

## How to inspect some paths

```bash
INPUT_FILE="pathbuilder_wisski.xml"
uv run wisskas $INPUT_FILE paths --flat
uv run wisskas $INPUT_FILE paths --flat g_publication
uv run wisskas $INPUT_FILE paths --flat g_external_authority
uv run wisskas $INPUT_FILE paths --flat --all

uv run wisskas $INPUT_FILE paths --nested
uv run wisskas $INPUT_FILE paths --nested g_publication
uv run wisskas $INPUT_FILE paths --nested --all

# generate paths

# g_person entity and all its direct fields
uv run wisskas $INPUT_FILE endpoints --listing-include g_person '*'

# g_person entity and all its direct fields (except not crossing entity boundaries)
uv run wisskas $INPUT_FILE endpoints --listing-include g_person '%'

# g_person entity and all its direct and indirect fields, but not crossing entity boundaries (avoids recursion)
uv run wisskas $INPUT_FILE endpoints --listing-include g_person '%%'

# same, but selectively cross one entity boundary
uv run wisskas $INPUT_FILE endpoints --listing-include g_person '%%' 'g_person_id_assignment.g_person_id_assignment_by.*'
```
