from medifind.aliases import reviewed_aliases
from medifind.p2_sources import verify_expansion

if __name__ == "__main__":
    sample = verify_expansion()
    aliases = reviewed_aliases()
    print(
        f"P2 qualified sources: {len(sample.records)} presentations, "
        f"{len(sample.artifacts)} hashes, "
        f"{len(aliases)} reviewed English spellings. No clinical or current-stock proof."
    )
