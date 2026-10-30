import pytest

from app.config import Settings

KEY = "k" * 32


@pytest.mark.parametrize(
    "given, expected",
    [
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql://u:p@host/db?sslmode=require", "postgresql+psycopg://u:p@host/db?sslmode=require"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite://", "sqlite://"),
    ],
)
def test_database_url_gets_driver(given, expected):
    assert Settings(database_url=given, secret_key=KEY).database_url == expected


def test_short_secret_rejected():
    with pytest.raises(ValueError):
        Settings(secret_key="short")
