import pytest
from fastapi.testclient import TestClient
import os

from app.main import app
from app.database import init_db


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = tmp_path / "test.db"
    import app.database as dbmod
    dbmod.DB_PATH = str(db_path)
    init_db()
    yield
    if os.path.exists(str(db_path)):
        os.remove(str(db_path))


@pytest.fixture
def client():
    return TestClient(app)


class TestMaterials:
    def test_create_and_get(self, client):
        r = client.post("/materials/", json={"title": "Note A", "material_type": "note", "topic_summary": "topic"})
        assert r.status_code == 200
        mat = r.json()
        assert mat["title"] == "Note A"
        mid = mat["id"]

        r2 = client.get(f"/materials/{mid}")
        assert r2.status_code == 200
        assert r2.json()["title"] == "Note A"

    def test_list_empty(self, client):
        r = client.get("/materials/")
        assert r.status_code == 200
        assert r.json() == []

    def test_delete(self, client):
        r = client.post("/materials/", json={"title": "Delete Me", "material_type": "note"})
        mid = r.json()["id"]
        r2 = client.delete(f"/materials/{mid}")
        assert r2.status_code == 200
        r3 = client.get(f"/materials/{mid}")
        assert r3.status_code == 404

    def test_version_with_blocks(self, client):
        r = client.post("/materials/", json={"title": "Snippet X", "material_type": "snippet"})
        mat = r.json()
        mid = mat["id"]

        rv = client.post(f"/materials/{mid}/versions", json={"language": "py", "change_note": "init", "test_status": "untested"})
        assert rv.status_code == 200
        ver = rv.json()

        rb = client.post(
            f"/materials/{mid}/versions/{ver['id']}/blocks",
            json={"block_order": 0, "block_type": "code", "language": "py", "code_content": "x=1"},
        )
        assert rb.status_code == 200

        rd = client.get(f"/materials/{mid}")
        assert rd.status_code == 200
        detail = rd.json()
        assert len(detail["versions"]) == 1
        assert len(detail["versions"][0]["blocks"]) == 1
        assert detail["versions"][0]["blocks"][0]["code_content"] == "x=1"

    def test_tagging(self, client):
        r = client.post("/materials/", json={"title": "Tagged", "material_type": "note"})
        mid = r.json()["id"]

        rt = client.post(f"/materials/{mid}/tags", json={"tag_name": "python"})
        assert rt.status_code == 200

        rg = client.get(f"/materials/{mid}/tags")
        assert rg.status_code == 200
        assert any(t["name"] == "python" for t in rg.json())

    def test_relations(self, client):
        r1 = client.post("/materials/", json={"title": "A", "material_type": "note"})
        r2 = client.post("/materials/", json={"title": "B", "material_type": "note"})
        mid1 = r1.json()["id"]
        mid2 = r2.json()["id"]

        rr = client.post(f"/materials/{mid1}/relations", json={"to_material_id": mid2, "relation_type": "related"})
        assert rr.status_code == 200

        rels = client.get(f"/materials/{mid1}/relations").json()
        assert len(rels) == 1
        assert rels[0]["id"] == mid2


class TestSearch:
    def test_search_and_suggest(self, client):
        client.post("/materials/", json={"title": "FastAPI basics", "material_type": "note", "topic_summary": "web framework"})

        r = client.get("/search/", params={"q": "FastAPI"})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 1
        assert any("FastAPI" in m["title"] for m in data["results"])

        rs = client.get("/search/suggest", params={"q": "Fast"})
        assert rs.status_code == 200
        assert len(rs.json()) >= 1

    def test_recent(self, client):
        r = client.get("/materials/recent")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
