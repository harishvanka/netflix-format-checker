import pytest

import scripts.unogs_prototype as up


class DummyResp:
    def __init__(self, json_data=None, status=200):
        self._json = json_data or {}
        self.status = status

    def raise_for_status(self):
        if not (200 <= self.status < 300):
            raise Exception("http error")

    def json(self):
        return self._json


def test_get_unogs_results_filters_by_mode(monkeypatch):
    # Prepare fake provider response
    fake = {"results": [
        {"title": "Coming Movie", "start_date": "2025-12-25"},
        {"title": "Leaving Movie", "end_date": "2025-12-28"},
        {"title": "NoDate"},
    ]}

    def fake_get(url, headers=None, params=None, timeout=None):
        return DummyResp(fake)

    monkeypatch.setattr(up.requests, "get", fake_get)
    # Set env key so function doesn't error
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")

    coming = up.get_unogs_results("coming")
    assert any(i.get("title") == "Coming Movie" for i in coming)
    assert all(i.get("title") != "Leaving Movie" for i in coming)

    leaving = up.get_unogs_results("leaving")
    assert any(i.get("title") == "Leaving Movie" for i in leaving)
    assert all(i.get("title") != "Coming Movie" for i in leaving)


def test_filter_by_languages():
    items = [
        {"title": "A", "spoken_languages": ["hi", "en"]},
        {"title": "B", "spoken_languages": ["fr"]},
    ]
    res = up.filter_by_languages(items, ["hi", "ta"])
    assert len(res) == 1
    assert res[0]["title"] == "A"


def test_enrich_with_tmdb(monkeypatch):
    # Monkeypatch Session to return controlled search and details
    class FakeSession:
        def get(self, url, params=None, timeout=None):
            if url.endswith("/search/multi"):
                return DummyResp({"results": [{"id": 42, "media_type": "movie", "title": "X"}]})
            elif url.endswith("/movie/42"):
                return DummyResp({"spoken_languages": [{"iso_639_1": "hi"}]})
            return DummyResp({})

    monkeypatch.setenv("TMDB_API_KEY", "tmdb-test")
    monkeypatch.setattr(up.requests, "Session", lambda: FakeSession())

    items = [{"title": "X"}]
    enriched = up.enrich_with_tmdb(items, "tmdb-test")
    assert enriched[0].get("spoken_languages") == ["hi"]
