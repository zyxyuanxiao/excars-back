import asyncio

from excars import repositories
from excars.models.profiles import Role
from excars.models.rides import RideRequest, RideRequestStatus


def test_create_ride_request(client, profile_factory, make_token_headers):
    receiver = profile_factory()
    sender = profile_factory(role=Role.opposite(receiver.role))

    with client as cli:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repositories.profile.save(cli.app.redis_cli, receiver))
        loop.run_until_complete(repositories.profile.save(cli.app.redis_cli, sender))
        headers = make_token_headers(sender.user_id)
        response = cli.post("/api/v1/rides", headers=headers, json={"receiver": receiver.user_id})

    assert response.status_code == 200
    assert RideRequest(**response.json())


def test_create_ride_request_raises_404(client, faker, make_token_headers):
    with client as cli:
        response = cli.post("/api/v1/rides", headers=make_token_headers(), json={"receiver": faker.pyint()})
    assert response.status_code == 404


def test_create_ride_request_when_sender_is_not_joined(client, profile_factory, make_token_headers):
    receiver = profile_factory()

    with client as cli:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repositories.profile.save(cli.app.redis_cli, receiver))
        response = cli.post("/api/v1/rides", headers=make_token_headers(), json={"receiver": receiver.user_id})

    assert response.status_code == 200
    assert RideRequest(**response.json())


def test_update_ride(client, profile_factory, make_token_headers):
    receiver = profile_factory(role=Role.hitchhiker)
    sender = profile_factory(role=Role.opposite(receiver.role))
    ride_request = RideRequest(sender=sender, receiver=receiver, status=RideRequestStatus.requested)

    with client as cli:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repositories.profile.save(cli.app.redis_cli, receiver))
        loop.run_until_complete(repositories.profile.save(cli.app.redis_cli, sender))
        loop.run_until_complete(repositories.rides.create_request(cli.app.redis_cli, ride_request))
        headers = make_token_headers(receiver.user_id)
        response = cli.put(
            f"/api/v1/rides/{ride_request.ride_uid}",
            headers=headers,
            json={"status": RideRequestStatus.accepted.value},
        )

    assert response.status_code == 200
    assert RideRequest(**response.json())


def test_update_ride_receiver_not_found(client, faker, make_token_headers):
    with client as cli:
        response = cli.put(
            f"/api/v1/rides/{faker.pyint()}",
            headers=make_token_headers(),
            json={"status": RideRequestStatus.accepted.value},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Receiver not found."}


def test_update_ride_sender_not_found(client, faker, profile_factory, make_token_headers):
    receiver = profile_factory(role=Role.hitchhiker)
    with client as cli:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repositories.profile.save(cli.app.redis_cli, receiver))
        headers = make_token_headers(receiver.user_id)
        response = cli.put(
            f"/api/v1/rides/{faker.pyint()}", headers=headers, json={"status": RideRequestStatus.accepted.value}
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Sender not found."}


def test_update_ride_ride_request_not_found(client, profile_factory, make_token_headers):
    receiver = profile_factory(role=Role.hitchhiker)
    sender = profile_factory(role=Role.opposite(receiver.role))
    with client as cli:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repositories.profile.save(cli.app.redis_cli, receiver))
        loop.run_until_complete(repositories.profile.save(cli.app.redis_cli, sender))
        headers = make_token_headers(receiver.user_id)
        response = cli.put(
            f"/api/v1/rides/{sender.user_id}", headers=headers, json={"status": RideRequestStatus.accepted.value}
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Ride request not found."}
