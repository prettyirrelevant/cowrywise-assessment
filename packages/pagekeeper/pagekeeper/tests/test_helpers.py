import datetime

from time_machine import travel

from pagekeeper.helpers import (
    create_token,
    verify_token,
    hash_password,
    verify_password,
    generate_user_identifier,
)


def test_create_and_verify_token() -> None:
    secret = 'test_secret'
    user_id = 'test_user'
    is_admin = False
    expiration = datetime.timedelta(hours=1)

    token = create_token(secret=secret, user_id=user_id, is_admin=is_admin, expiration=expiration)
    payload = verify_token(token=token, secret=secret)

    assert payload is not None
    assert payload['user_id'] == user_id
    assert payload['is_admin'] == is_admin


def test_verify_token_expired() -> None:
    secret = 'test_secret'
    user_id = 'test_user'
    is_admin = False
    expiration = datetime.timedelta(hours=5)

    token = create_token(secret=secret, user_id=user_id, is_admin=is_admin, expiration=expiration)
    with travel(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)):
        payload = verify_token(token=token, secret=secret)
        assert payload is None


def test_verify_token_invalid() -> None:
    secret = 'test_secret'
    invalid_token = 'invalid.token.here'

    payload = verify_token(token=invalid_token, secret=secret)
    assert payload is None


def test_generate_user_identifier() -> None:
    identifier = generate_user_identifier()
    assert identifier.startswith('user_')
    assert len(identifier) == 27


def test_verify_password_success() -> None:
    password = 'test_password'
    hashed = hash_password(password)
    assert verify_password(expected_password=password, actual_hash=hashed)


def test_verify_password_failure() -> None:
    password = 'test_password'
    wrong_password = 'wrong_password'
    hashed = hash_password(password)
    assert not verify_password(expected_password=wrong_password, actual_hash=hashed)


def test_hash_password() -> None:
    password = 'test_password'
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(expected_password=password, actual_hash=hashed)


def test_create_token_different_expirations() -> None:
    secret = 'test_secret'
    user_id = 'test_user'
    is_admin = False

    short_exp = datetime.timedelta(minutes=5)
    long_exp = datetime.timedelta(days=1)

    short_token = create_token(secret=secret, user_id=user_id, is_admin=is_admin, expiration=short_exp)
    long_token = create_token(secret=secret, user_id=user_id, is_admin=is_admin, expiration=long_exp)

    assert short_token != long_token

    short_payload = verify_token(token=short_token, secret=secret)
    long_payload = verify_token(token=long_token, secret=secret)

    assert short_payload['exp'] < long_payload['exp']


def test_verify_token_different_secrets() -> None:
    user_id = 'test_user'
    is_admin = False
    expiration = datetime.timedelta(hours=1)

    token1 = create_token(secret='secret1', user_id=user_id, is_admin=is_admin, expiration=expiration)
    token2 = create_token(secret='secret2', user_id=user_id, is_admin=is_admin, expiration=expiration)

    assert verify_token(token=token1, secret='secret1') is not None
    assert verify_token(token=token2, secret='secret2') is not None
    assert verify_token(token=token1, secret='secret2') is None
    assert verify_token(token=token2, secret='secret1') is None
