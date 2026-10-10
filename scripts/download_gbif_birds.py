#!/usr/bin/env python3
"""Download a manageable sample of georeferenced bird records from GBIF.

The geographic filter is an approximate bounding box around Kharkiv Oblast,
not an official administrative boundary. Some records may be outside the oblast.
"""

import csv
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://api.gbif.org/v1/occurrence/search"
MAX_RECORDS = 3000
PAGE_SIZE = 300

# Approximate bounding box for an initial experiment.
# TODO: replace this rectangle with the official oblast polygon.
FILTERS = {
    "taxonKey": 212,  # Aves (birds) in GBIF's taxonomic backbone
    "country": "UA",
    "hasCoordinate": "true",
    "decimalLatitude": "48.5,50.5",
    "decimalLongitude": "34.5,38.5",
}

FIELDS = [
    "gbifID",
    "scientificName",
    "vernacularName",
    "eventDate",
    "countryCode",
    "stateProvince",
    "locality",
    "decimalLatitude",
    "decimalLongitude",
    "coordinateUncertaintyInMeters",
    "basisOfRecord",
    "datasetKey",
    "occurrenceID",
]


def fetch_page(offset: int, limit: int) -> dict:
    """Request one page of results from the public GBIF Occurrence API."""
    params = {**FILTERS, "limit": limit, "offset": offset}
    url = f"{API_URL}?{urlencode(params)}"
    request = Request(
        url,
        headers={"User-Agent": "kharkiv-birds-atlas/0.1 (educational project)"},
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    output_path = Path(__file__).resolve().parent.parent / "data" / "gbif_birds_sample.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    offset = 0
    target = MAX_RECORDS

    print("Requesting bird occurrence records from GBIF...")
    print("Note: the geographic rectangle is approximate, not the official oblast border.")

    while len(records) < target:
        page_limit = min(PAGE_SIZE, target - len(records))
        page = fetch_page(offset, page_limit)
        results = page.get("results", [])

        if not results:
            break

        records.extend(results)
        offset += len(results)
        total = page.get("count", "unknown")
        print(f"Retrieved {len(records)} records so far (GBIF reports {total} matches).")

        if len(results) < page_limit:
            break

        # Be polite to the public API between requests.
        time.sleep(0.2)

    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in FIELDS})

    print(f"Saved {len(records)} records to: {output_path}")
    print("Remember: occurrence records show reported records, not bird population sizes.")


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"Could not retrieve data from GBIF: {error}")
        print("Check your internet connection and try again.")
