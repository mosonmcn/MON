"""Route map only -- fast, no raw files saved, no JS/API analysis."""

from mon import inspect

result = inspect(
    domain="example.com",
    action="explorer_visual",
    profile="fast",
    save=False,
)

print(result.explorer_visual)
