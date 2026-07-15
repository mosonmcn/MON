"""API specification only -- no raw HTML/CSS/asset files saved."""

from mon import inspect

result = inspect(
    domain="example.com",
    action="api_spec",
    profile="balanced",
    output_format="markdown",
    output_dir="./output",
    overwrite=True,
)

for endpoint in result.apis:
    print(f"{endpoint.method:6s} {endpoint.url}  (confidence: {endpoint.confidence.score}%)")
