"""
Collector simulator for local development.

Cycles through all fixture JSON files in FIXTURE_DIR and POSTs each
to the KubeOpt API as a collector report on every interval.

Used by docker-compose.dev.yml to prove the full push flow without a
real cluster.
"""

import json
import logging
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("collector-sim")

API_URL = os.environ.get("KUBEOPT_API_URL", "http://localhost:5010").rstrip("/")
TOKEN = os.environ.get("KUBEOPT_TOKEN", "")
FIXTURE_DIR = Path(os.environ.get("FIXTURE_DIR", "/fixtures"))
INTERVAL = int(os.environ.get("INTERVAL_SECONDS", "30"))


def load_fixtures():
    fixtures = sorted(FIXTURE_DIR.glob("collector_report_*.json"))
    if not fixtures:
        log.warning("no collector_report_*.json fixtures found in %s", FIXTURE_DIR)
    return fixtures


def post_report(payload: bytes, fixture_name: str):
    req = urllib.request.Request(
        f"{API_URL}/api/collector/report",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body = json.loads(r.read())
            log.info("accepted [%s]: cluster=%s nodes=%s pods=%s",
                     fixture_name, body.get("cluster_id"), body.get("nodes"), body.get("pods"))
    except urllib.error.HTTPError as e:
        log.error("HTTP %d for %s: %s", e.code, fixture_name, e.read().decode())
    except Exception as e:
        log.error("error posting %s: %s", fixture_name, e)


def main():
    log.info("collector simulator starting (api=%s, interval=%ds)", API_URL, INTERVAL)
    while True:
        fixtures = load_fixtures()
        for fixture in fixtures:
            try:
                payload = fixture.read_bytes()
                post_report(payload, fixture.name)
            except Exception as e:
                log.error("failed to read %s: %s", fixture, e)
        if fixtures:
            log.info("cycle complete (%d fixtures) -- sleeping %ds", len(fixtures), INTERVAL)
        time.sleep(INTERVAL)


main()
