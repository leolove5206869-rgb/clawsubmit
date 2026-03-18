from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_parse_returns_fixed_schema():
    response = client.post("/parse", json={"message": "demo", "attachment_path": "/samples/invoice.jpg"})
    assert response.status_code == 200
    data = response.json()
    assert data["expense_type"] == "差旅-打车"
    assert data["amount"] == "86.50"
    assert data["attachment_path"] == "/samples/invoice.jpg"


def test_plan_returns_fixed_checklist():
    fields = client.post("/parse", json={"message": "demo"}).json()
    response = client.post("/plan", json={"fields": fields})
    assert response.status_code == 200
    checklist = response.json()["checklist"]
    assert checklist[0] == "打开报销系统并进入新建报销单"
    assert checklist[-1] == "回写回执消息到本地聊天面板"


def test_expense_pages_render_expected_data():
    new_page = client.get("/expense/new")
    assert new_page.status_code == 200
    assert 'data-testid="submit-expense"' in new_page.text

    detail_page = client.get("/expense/BX-20260318-0042")
    assert detail_page.status_code == 200
    assert "BX-20260318-0042" in detail_page.text
    assert "待审批" in detail_page.text
