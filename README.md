# MON -- Moson Web Intelligence Engine

MON is a modular Python framework for inspecting websites: understanding
frontend architecture, discovering backend APIs, generating API
documentation, reconstructing application structure, and exporting
structured knowledge -- e.g. for feeding into an AI agent.

It is not a website cloner. Cloning raw files is one small action among
twelve; MON's real job is *reconstruction*: turning a live website back into
a structured, documented, machine-readable specification of how it works.

## Install

```bash
pip install -r requirements.txt
# or, for development (adds pytest):
pip install -e ".[dev]"
```

## Usage

MON exposes exactly one public function.

```python
from mon import inspect

result = inspect(
    domain="example.com",
    action="all_data",       # or e.g. ["explorer", "api_spec", "technology"]
    profile="balanced",      # "fast" | "balanced" | "deep"
    output_format="json",    # "python" | "json" | "markdown" | "html" | "yaml"
    output_dir="./output",
)

print(result.apis)           # list[Endpoint]
print(result.forms)          # list[Form]
print(result.routes)         # list[Route]
print(result.technology)     # list[Technology]
print(result.explorer_visual)
```

See `examples/` for more: `basic.py`, `explorer.py`, `api_spec.py`, `all_data.py`.

## Architecture

```
User -> inspect() -> SDK -> Inspector -> Resolver -> Dispatcher -> Analyzers -> Context -> Exporter -> InspectResult
```

- **SDK** (`mon/sdk.py`) -- the only public entry point. Builds config, calls
  Inspector, optionally saves output.
- **Inspector** (`mon/engine/inspector.py`) -- orchestrates the run. Knows
  nothing about HTML/JS/APIs.
- **Resolver** (`mon/engine/resolver.py`) -- expands composite actions
  (e.g. `api_spec`) and topologically sorts analyzers by declared
  dependencies, so `javascript` always runs before `api`, which always runs
  before `relationships`.
- **Registry** (`mon/engine/registry.py`) -- maps action names to analyzer
  classes. Adding a new analyzer never requires touching the Dispatcher.
- **Dispatcher** (`mon/engine/dispatcher.py`) -- executes the resolved
  pipeline against one shared `InspectContext`.
- **Context** (`mon/engine/context.py`) -- the only channel analyzers use to
  communicate. No analyzer ever imports another analyzer.
- **Events** (`mon/engine/events.py`) -- analyzers never call `print()`;
  they emit events, and `ProgressManager` (or a future plugin/AI layer)
  subscribes.
- **Analyzers** (`mon/analyzers/`) -- one class per file, one responsibility
  each: crawler, html, javascript, forms, api, routes, assets, metadata,
  technology, server, relationships, explorer.
- **Exporters** (`mon/exporters/`) -- turn an `InspectResult` into
  Python/JSON/Markdown/HTML/YAML.

## Actions

Leaf actions: `crawler`, `html`, `javascript`, `forms`, `api`, `routes`,
`assets`, `metadata`, `technology`, `server_info`, `relationships`, `explorer`.

Composite actions: `all_data`, `frontend`, `backend`, `api_spec`,
`explorer_visual`, `cloning`.

## Confidence scoring

Every `Endpoint` carries a `confidence.score` (0-100) and
`confidence.reasons` -- a list of exactly why MON believes the endpoint is
real (e.g. *"Success/error branches detected in JS"*, *"Matched to HTML form"*,
*"Live-verified against server"*). Nothing is asserted without a reason.

## License

MIT -- see `LICENSE`.
