import asyncio
import random

from excars import repositories
from excars.models.profiles import Profile, Role


def test_join(client, faker, token_headers):
    with client as cli:
        response = cli.post(
            "/api/v1/profiles",
            headers=token_headers,
            json={
                "role": random.choice([Role.driver, Role.hitchhiker]),
                "destination": {
                    "name": faker.name(),
                    "latitude": str(faker.latitude()),
                    "longitude": str(faker.longitude()),
                },
            },
        )

    assert response.status_code == 200
    assert response.json()["role"] == "driver"


def test_get_profile(client, profile_factory, token_headers):
    profile = profile_factory()

    with client as cli:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repositories.profile.save(cli.app.redis_cli, profile))
        response = cli.get(f"/api/v1/profiles/{profile.user_id}", headers=token_headers)

    assert response.status_code == 200
    assert Profile(**response.json()) == profile


def test_get_profile_returns_404(client, faker, token_headers):
    with client as cli:
        response = cli.get(f"/api/v1/profiles/{faker.pyint()}", headers=token_headers)
    assert response.status_code == 404
