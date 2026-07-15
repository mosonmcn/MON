"""Full inspection using an explicit action list instead of the 'all_data' shortcut."""

from mon import inspect

result = inspect(
    domain="example.com",
    action=["explorer", "api_spec", "technology", "server_info"],
    profile="deep",
    output_format="json",
    output_dir="./output",
    project_name="example_com_full_report",
    overwrite=True,
)

print(f"Actions run: {result.actions_run}")
print(f"Relationship chains reconstructed: {len(result.relationships)}")
for chain in result.relationships:
    print(" ", chain.describe())
