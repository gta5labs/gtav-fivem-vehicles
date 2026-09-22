#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
from datetime import datetime, timezone
from html.parser import HTMLParser
import html
import json
from pathlib import Path
import re
import sys
import time
from urllib.request import Request, urlopen

SOURCE_URL = "https://docs.fivem.net/docs/game-references/vehicle-references/vehicle-models/"
IMAGE_ROOT = "https://docs-backend.fivem.net/vehicles/"
USER_AGENT = "FiveLabs-VehicleDB/1.0"

ROOT = Path(__file__).resolve().parent
VEHICLES_DIR = ROOT / "vehicles"
INDEX_JSON = VEHICLES_DIR / "index.json"
INDEX_JS = VEHICLES_DIR / "index.js"

ENTRY_RE = re.compile(
    r"Display\s*Name:\s*(.*?)\s+Hash:\s*(-?\d+)\s+Model\s*Name:\s*([A-Za-z0-9_-]+)",
    re.I | re.S
)

def clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()

class FiveMVehicleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_h2 = False
        self.heading_parts = []
        self.category = None
        self.buffer = []
        self.records = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "h2":
            self.in_h2 = True
            self.heading_parts = []

    def handle_endtag(self, tag):
        if tag.lower() == "h2" and self.in_h2:
            heading = clean(" ".join(self.heading_parts))
            if heading and heading.lower() != "vehicle models":
                self.category = heading
            self.in_h2 = False
            self.heading_parts = []
            self.buffer = []

    def handle_data(self, data):
        text = clean(data)
        if not text:
            return

        if self.in_h2:
            self.heading_parts.append(text)
            return

        if not self.category:
            return

        self.buffer.append(text)
        merged = clean(" ".join(self.buffer))

        if len(merged) > 1000:
            merged = merged[-1000:]
            self.buffer = [merged]

        match = ENTRY_RE.search(merged)
        if not match:
            return

        display_name = clean(match.group(1))
        raw_hash = int(match.group(2))
        model = match.group(3).lower()

        unsigned_hash = raw_hash & 0xFFFFFFFF

        self.records.append({
            "model": model,
            "displayName": display_name,
            "hash": str(unsigned_hash),
            "signedHash": raw_hash if raw_hash < 0 else (raw_hash - 0x100000000 if raw_hash > 0x7FFFFFFF else raw_hash),
            "hexHash": f"0x{unsigned_hash:08X}",
            "path": f"vehicles/{model}.webp"
        })

        self.buffer = []

def download_text(url: str) -> str:
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,*/*",
        "Cache-Control": "no-cache"
    })
    with urlopen(req, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")

def download_image(model: str, overwrite: bool = False):
    target = VEHICLES_DIR / f"{model}.webp"

    if target.exists() and target.stat().st_size > 200 and not overwrite:
        return model, True, "cached"

    url = IMAGE_ROOT + model + ".webp"
    error = ""

    for attempt in range(4):
        try:
            req = Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "image/webp,image/*,*/*",
                "Referer": SOURCE_URL
            })
            with urlopen(req, timeout=45) as response:
                data = response.read()

            if len(data) < 200:
                raise RuntimeError("response too small")

            if not (data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
                raise RuntimeError("response is not WebP")

            temp = target.with_suffix(".webp.tmp")
            temp.write_bytes(data)
            temp.replace(target)
            return model, True, f"{len(data) // 1024} KB"

        except Exception as exc:
            error = str(exc)
            if attempt < 3:
                time.sleep(1.5 * (2 ** attempt))

    return model, False, error

def parse_official_page(markup: str):
    parser = FiveMVehicleParser()
    parser.feed(markup)

    categories = {}
    seen = set()

    # Re-parse with category context to preserve exact grouping.
    # The parser stores records in page order; we walk the raw page by H2 section.
    section_re = re.compile(
        r"<h2[^>]*>(.*?)</h2>(.*?)(?=<h2[^>]*>|$)",
        re.I | re.S
    )

    tag_re = re.compile(r"<[^>]+>")
    for heading_html, section_html in section_re.findall(markup):
        heading = clean(tag_re.sub(" ", heading_html))
        if not heading or heading.lower() == "vehicle models":
            continue

        section_text = clean(tag_re.sub(" ", section_html))
        items = []

        for match in ENTRY_RE.finditer(section_text):
            display_name = clean(match.group(1))
            raw_hash = int(match.group(2))
            model = match.group(3).lower()

            if model in seen:
                continue

            seen.add(model)
            unsigned_hash = raw_hash & 0xFFFFFFFF

            items.append({
                "model": model,
                "displayName": display_name,
                "hash": str(unsigned_hash),
                "signedHash": raw_hash if raw_hash < 0 else (raw_hash - 0x100000000 if raw_hash > 0x7FFFFFFF else raw_hash),
                "hexHash": f"0x{unsigned_hash:08X}",
                "path": f"vehicles/{model}.webp"
            })

        if items:
            categories[heading] = items

    # Fallback to HTMLParser records if docs markup changes enough that section regex fails.
    if sum(map(len, categories.values())) < 100:
        categories = {}
        current = None

        # Use a second tiny parser that binds entries to headings through text flow.
        class FlowParser(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.in_h2 = False
                self.h2 = []
                self.category = None
                self.buf = []
                self.out = {}

            def handle_starttag(self, tag, attrs):
                if tag.lower() == "h2":
                    self.in_h2 = True
                    self.h2 = []

            def handle_endtag(self, tag):
                if tag.lower() == "h2":
                    heading = clean(" ".join(self.h2))
                    if heading and heading.lower() != "vehicle models":
                        self.category = heading
                        self.out.setdefault(heading, [])
                    self.in_h2 = False
                    self.buf = []

            def handle_data(self, data):
                value = clean(data)
                if not value:
                    return
                if self.in_h2:
                    self.h2.append(value)
                    return
                if not self.category:
                    return

                self.buf.append(value)
                merged = clean(" ".join(self.buf))
                match = ENTRY_RE.search(merged)

                if match:
                    display_name = clean(match.group(1))
                    raw_hash = int(match.group(2))
                    model = match.group(3).lower()
                    unsigned_hash = raw_hash & 0xFFFFFFFF
                    self.out[self.category].append({
                        "model": model,
                        "displayName": display_name,
                        "hash": str(unsigned_hash),
                        "signedHash": raw_hash if raw_hash < 0 else (raw_hash - 0x100000000 if raw_hash > 0x7FFFFFFF else raw_hash),
                        "hexHash": f"0x{unsigned_hash:08X}",
                        "path": f"vehicles/{model}.webp"
                    })
                    self.buf = []

        flow = FlowParser()
        flow.feed(markup)
        categories = flow.out

    # Final dedupe.
    clean_categories = {}
    global_seen = set()

    for category, items in categories.items():
        output = []
        for item in items:
            if item["model"] in global_seen:
                continue
            global_seen.add(item["model"])
            output.append(item)
        if output:
            clean_categories[category] = output

    return clean_categories

def write_indexes(categories, failures):
    count = sum(len(items) for items in categories.values())

    payload = {
        "meta": {
            "source": SOURCE_URL,
            "imageSource": IMAGE_ROOT + "{model}.webp",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "vehicleCount": count,
            "categoryCount": len(categories),
            "missingPreviews": sorted(failures)
        },
        "categories": categories
    }

    INDEX_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    INDEX_JS.write_text(
        "window.VEHICLE_DB = " +
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) +
        ";\n",
        encoding="utf-8"
    )

def self_test():
    sample = """
    <h1>Vehicle Models</h1>
    <h2>Compacts</h2>
    <p>Display Name: Asbo Hash: 1118611807 Model Name: asbo</p>
    <p>Display Name: Blista Hash: 3950024287 Model Name: blista</p>
    <h2>Sedans</h2>
    <p>Display Name: Asea Hash: 2485144969 Model Name: asea</p>
    """
    categories = parse_official_page(sample)
    assert categories["Compacts"][0]["model"] == "asbo"
    assert categories["Compacts"][1]["model"] == "blista"
    assert categories["Sedans"][0]["model"] == "asea"
    assert sum(len(x) for x in categories.values()) == 3
    print("Parser self-test passed.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    VEHICLES_DIR.mkdir(parents=True, exist_ok=True)

    print("============================================================")
    print(" FiveLabs Vehicle DB - Official FiveM Database Setup")
    print("============================================================")
    print()
    print("Vehicle data:")
    print("  " + SOURCE_URL)
    print("Preview images:")
    print("  " + IMAGE_ROOT + "{model}.webp")
    print()

    print("[1/4] Downloading official FiveM vehicle page...")
    markup = download_text(SOURCE_URL)

    print("[2/4] Reading vehicle categories and models...")
    categories = parse_official_page(markup)
    count = sum(len(items) for items in categories.values())

    if count < 500:
        raise RuntimeError(
            f"Only {count} vehicle records were found. "
            "The FiveM documentation format may have changed, so setup was stopped "
            "instead of creating an incomplete database."
        )

    print(f"      Found {count} vehicles in {len(categories)} categories.")

    models = [item["model"] for items in categories.values() for item in items]

    print("[3/4] Downloading official preview images...")
    failures = []

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max(1, min(args.workers, 20))
    ) as executor:
        jobs = [
            executor.submit(download_image, model, args.overwrite)
            for model in models
        ]

        completed = 0

        for job in concurrent.futures.as_completed(jobs):
            model, ok, detail = job.result()
            completed += 1

            if not ok:
                failures.append(model)

            state = "OK" if ok else "MISS"
            print(
                f"\r      [{completed:>4}/{count}] {state:<4} {model:<24} {detail[:45]:<45}",
                end="",
                flush=True
            )

    print()
    print("[4/4] Writing vehicles/index.json + vehicles/index.js...")
    write_indexes(categories, failures)

    preview_count = count - len(failures)

    print()
    print("Done.")
    print(f"  Vehicles : {count}")
    print(f"  Categories: {len(categories)}")
    print(f"  Previews : {preview_count}/{count}")
    print()
    print("Open index.html to preview the database.")
    print("For GitHub Pages, commit this whole folder and deploy from your branch.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(130)
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
