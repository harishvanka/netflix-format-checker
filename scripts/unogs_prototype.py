#!/usr/bin/env python3
"""Prototype CLI to query uNoGS via RapidAPI and filter for coming/leaving titles in India.

Usage:
  RAPIDAPI_KEY and RAPIDAPI_HOST must be set in the environment. Optionally set TMDB_API_KEY

Examples:
  python scripts/unogs_prototype.py --mode coming
  python scripts/unogs_prototype.py --mode leaving --enrich
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from typing import List, Dict, Any, Optional

import requests


def get_unogs_results(mode: str, country: str = "IN", days: int = 30) -> List[Dict[str, Any]]:
    """Query uNoGS via RapidAPI and return result items.

    mode: 'coming' or 'leaving'
    """
    api_key = os.environ.get("RAPIDAPI_KEY")
    api_host = os.environ.get("RAPIDAPI_HOST", "unogsng.p.rapidapi.com")
    if not api_key:
        raise RuntimeError("RAPIDAPI_KEY is not set in environment")

    today = datetime.date.today()
    start = today
    end = today + datetime.timedelta(days=days)

    # Provider param names can vary; this is a best-effort example
    params = {
        "countrylist": country,
        # Documentation-dependent: try `start_date` and `end_date` if present
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "order_by": "date",
        "type": "movie,tv",
    }

    # Use the /search or /titles endpoint depending on provider; /search is common on RapidAPI
    url = f"https://{api_host}/search"
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": api_host}

    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Typical providers return a 'results' key
    results = data.get("results") or data.get("items") or []

    # Heuristic: filter by date fields depending on mode
    out: List[Dict[str, Any]] = []
    for item in results:
        # providers differ; try to find relevant date fields
        start_date = item.get("start_date") or item.get("first_air_date") or item.get("released")
        end_date = item.get("end_date") or item.get("expiry") or item.get("expires")

        if mode == "coming":
            if start_date:
                out.append(item)
        elif mode == "leaving":
            if end_date:
                out.append(item)
        else:
            raise ValueError("mode must be 'coming' or 'leaving'")

    return out


def enrich_with_tmdb(items: List[Dict[str, Any]], tmdb_key: Optional[str]) -> List[Dict[str, Any]]:
    """Optionally enrich result items with TMDB spoken languages.

    This implementation is intentionally simple: it attempts to match by title using TMDB search
    and then pulls details to get `spoken_languages`.
    """
    if not tmdb_key:
        return items

    session = requests.Session()
    base = "https://api.themoviedb.org/3"

    def get_spoken_codes(title: str) -> List[str]:
        q = session.get(f"{base}/search/multi", params={"api_key": tmdb_key, "query": title, "page": 1}, timeout=10)
        q.raise_for_status()
        j = q.json()
        results = j.get("results", [])
        if not results:
            return []
        # pick the best match (first)
        r = results[0]
        # fetch details
        typ = r.get("media_type") or ("movie" if r.get("title") else "tv")
        det = session.get(f"{base}/{typ}/{r['id']}", params={"api_key": tmdb_key}, timeout=10)
        det.raise_for_status()
        d = det.json()
        langs = d.get("spoken_languages") or []
        codes = [l.get("iso_639_1") for l in langs if l.get("iso_639_1")]
        return codes

    for it in items:
        title = it.get("title") or it.get("name")
        if not title:
            continue
        try:
            it["spoken_languages"] = get_spoken_codes(title)
        except Exception:
            it["spoken_languages"] = []

    return items


def filter_by_languages(items: List[Dict[str, Any]], langs: List[str]) -> List[Dict[str, Any]]:
    if not langs:
        return items
    langs_set = set(langs)
    out = []
    for it in items:
        codes = set([c.lower() for c in (it.get("spoken_languages") or [])])
        if codes & langs_set:
            out.append(it)
    return out


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="uNoGS prototype: find coming / leaving Netflix titles in India")
    p.add_argument("--mode", choices=("coming", "leaving"), default="coming")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--enrich", action="store_true", help="Enrich with TMDB and add spoken_languages field")
    p.add_argument("--languages", type=str, help="Comma-separated ISO language codes to filter (e.g. hi,ta,te,ml)")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    args = parse_args(argv)

    try:
        items = get_unogs_results(args.mode, days=args.days)
    except Exception as e:
        print(f"Error querying uNoGS: {e}")
        return 2

    tmdb_key = os.environ.get("TMDB_API_KEY") if args.enrich else None
    if args.enrich:
        items = enrich_with_tmdb(items, tmdb_key)

    langs = []
    if args.languages:
        langs = [l.strip().lower() for l in args.languages.split(",") if l.strip()]
        items = filter_by_languages(items, langs)

    # Simple output
    for it in items:
        title = it.get("title") or it.get("name")
        sd = it.get("start_date") or it.get("first_air_date")
        ed = it.get("end_date") or it.get("expiry") or it.get("expires")
        langs_out = ",".join(it.get("spoken_languages", []))
        print(f"{title} | start={sd} | end={ed} | langs={langs_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())