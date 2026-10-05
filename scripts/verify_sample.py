from medifind.source_data import verify_sample

if __name__ == "__main__":
    sample = verify_sample()
    print(f"Source sample verified: {len(sample.records)} records, {len(sample.artifacts)} hashes.")
    print(
        "Source transcription only; clinical equivalence and current availability NOT_ESTABLISHED."
    )
