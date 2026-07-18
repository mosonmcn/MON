"""Entry point -- same domain/target as cloner's original main.py, now
running through MON's modular pipeline (config -> inspector -> resolver ->
dispatcher -> analyzers -> output_writer) instead of a flat script, while
every network call still goes through cloner's original fetch logic
(mon/network/fetcher.py).
"""

from mon import inspect

if __name__ == "__main__":
    result = inspect(
        domain="payfluxai.com.ng",
        action="all_data",
        profile="balanced",
        output_dir="./data",
        response=True,
    )

    print(f"\n[✔] Pages crawled: {result.pages_crawled}")
    print(f"[✔] Routes discovered: {len(result.routes)}")
    print(f"[✔] API endpoints reconstructed: {len(result.api_spec)}")
    print(f"[✔] Static assets: {result.assets_saved}")
    if result.warnings:
        print(f"[⚠] Warnings: {len(result.warnings)}")
