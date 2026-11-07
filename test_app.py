import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_add(client):
    assert client.get("/add/2/3").get_json() == {"result": 5}


def test_divide(client):
    assert client.get("/divide/9/3").get_json() == {"result": 3.0}


def test_divide_by_zero_returns_400(client):
    response = client.get("/divide/1/0")
    assert response.status_code == 400
    assert response.get_json() == {"error": "division by zero"}
