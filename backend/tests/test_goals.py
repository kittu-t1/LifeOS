def test_create_goal_auto_creates_workspace(client):
    response = client.post("/api/v1/goals", json={"title": "Build LifeOS MVP"})
    assert response.status_code == 201

    body = response.json()
    assert body["title"] == "Build LifeOS MVP"
    assert body["status"] == "not_started"
    assert body["progress"] == 0
    assert body["workspace_id"] is not None


def test_list_goals_returns_created_goals(client):
    client.post("/api/v1/goals", json={"title": "Prepare for Google Interview"})
    client.post("/api/v1/goals", json={"title": "Plan Europe Trip"})

    response = client.get("/api/v1/goals")
    assert response.status_code == 200
    titles = {g["title"] for g in response.json()}
    assert titles == {"Prepare for Google Interview", "Plan Europe Trip"}


def test_get_goal_by_id(client):
    created = client.post("/api/v1/goals", json={"title": "Lose 10kg"}).json()

    response = client.get(f"/api/v1/goals/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_goal_not_found(client):
    response = client.get("/api/v1/goals/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_workspace_is_fetchable_and_includes_goal(client):
    created = client.post("/api/v1/goals", json={"title": "Launch AI Startup"}).json()
    workspace_id = created["workspace_id"]

    response = client.get(f"/api/v1/workspaces/{workspace_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == workspace_id
    assert body["goal"]["id"] == created["id"]
    assert body["goal"]["title"] == "Launch AI Startup"


def test_workspace_not_found(client):
    response = client.get("/api/v1/workspaces/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
