"""Basic usage: inspect a domain and print a summary."""

from mon import inspect

result = inspect(
    domain="example.com",
    action="all_data",
    profile="balanced",
    response="info",
    save=True,
    output_dir="./output",
    overwrite=True,
)

print(f"Pages crawled: {result.pages_crawled}")
print(f"Endpoints found: {len(result.apis)}")
print(f"Forms found: {len(result.forms)}")
print(f"Technology: {[t.name for t in result.technology]}")
