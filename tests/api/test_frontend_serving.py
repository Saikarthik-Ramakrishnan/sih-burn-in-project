"""Serving the compiled SPA.

These exist because this path had no coverage at all and was broken: FastAPI
raised at app-creation time on the fallback route's union return annotation, so
the whole service failed to boot the moment a frontend build appeared. Nothing
caught it because `frontend/dist` did not exist during development.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sih26170.api.config import ServiceMode, Settings
from sih26170.api.main import create_app

INDEX_HTML = '<!doctype html><html><body><div id="root">SPA</div></body></html>'


@pytest.fixture
def dist(tmp_path: Path) -> Path:
    """A minimal stand-in for a Vite build."""
    build = tmp_path / "dist"
    (build / "assets").mkdir(parents=True)
    (build / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (build / "assets" / "app.css").write_text("body{color:red}", encoding="utf-8")
    (build / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (build / "favicon.ico").write_bytes(b"\x00\x00\x01\x00")
    return build


@pytest.fixture
def built_client(dist: Path) -> TestClient:
    app = create_app(Settings(mode=ServiceMode.DEMO, frontend_dist_dir=dist))
    with TestClient(app) as client:
        yield client


@pytest.fixture
def unbuilt_client(tmp_path: Path) -> TestClient:
    app = create_app(
        Settings(mode=ServiceMode.DEMO, frontend_dist_dir=tmp_path / "absent")
    )
    with TestClient(app) as client:
        yield client


# --------------------------------------------------------------------------
# With a build present
# --------------------------------------------------------------------------


def test_app_can_be_created_when_a_build_exists(dist: Path):
    """Regression: create_app() used to raise FastAPIError here."""
    app = create_app(Settings(mode=ServiceMode.DEMO, frontend_dist_dir=dist))
    assert app is not None


def test_index_is_served_at_root(built_client: TestClient):
    response = built_client.get("/")
    assert response.status_code == 200
    assert "SPA" in response.text


def test_static_assets_are_served(built_client: TestClient):
    response = built_client.get("/assets/app.css")
    assert response.status_code == 200
    assert response.text == "body{color:red}"


def test_client_side_routes_fall_back_to_index(built_client: TestClient):
    """A deep link the SPA router owns must return index.html, not a 404."""
    for path in ("/dashboard", "/dashboard/batch/7", "/reports/2026/09"):
        response = built_client.get(path)
        assert response.status_code == 200, path
        assert "SPA" in response.text


def test_real_files_win_over_the_fallback(built_client: TestClient):
    response = built_client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.content == b"\x00\x00\x01\x00"


def test_api_still_works_with_a_build_present(built_client: TestClient):
    response = built_client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_api_404_stays_json_and_is_not_swallowed_by_the_spa(built_client: TestClient):
    """The SPA fallback must never turn a wrong API path into index.html."""
    response = built_client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["error"] == "NOT_FOUND"
    assert "SPA" not in response.text


def test_openapi_still_published_with_a_build_present(built_client: TestClient):
    response = built_client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert "/api/v1/screen" in response.json()["paths"]


# --------------------------------------------------------------------------
# Without a build
# --------------------------------------------------------------------------


def test_missing_build_does_not_block_the_api(unbuilt_client: TestClient):
    assert unbuilt_client.get("/api/v1/health/live").status_code == 200


def test_root_reports_the_frontend_is_not_built(unbuilt_client: TestClient):
    response = unbuilt_client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["frontend"] == "not built"
    assert body["openapi"] == "/api/v1/openapi.json"
