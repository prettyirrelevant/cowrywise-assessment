import datetime

import jwt
import pymongo
import shortuuid
from argon2 import PasswordHasher
from pymongo import MongoClient
from pymongo.database import Database
from argon2.exceptions import VerifyMismatchError


def create_token(*, secret: str, user_id: str, is_admin: bool, expiration: datetime.timedelta) -> str:
    payload = {
        'user_id': user_id,
        'is_admin': is_admin,
        'exp': datetime.datetime.now(datetime.UTC) + expiration,
    }
    return jwt.encode(payload, secret, algorithm='HS256')


def verify_token(*, token: str, secret: str) -> dict[str, str] | None:
    try:
        return jwt.decode(token, secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def initialize_database(*, url: str, db_name: str) -> Database:
    client = MongoClient(url)
    database = client[db_name]

    database.users.create_index([('email', pymongo.ASCENDING)], unique=True)
    return database


def generate_user_identifier() -> str:
    return f'user_{shortuuid.uuid()}'


def verify_password(*, expected_password: str, actual_hash: str) -> bool:
    try:
        ph = PasswordHasher()
        return ph.verify(actual_hash, expected_password)
    except VerifyMismatchError:
        return False


def hash_password(pw: str) -> str:
    ph = PasswordHasher()
    return ph.hash(pw)
