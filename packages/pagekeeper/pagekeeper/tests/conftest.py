from secrets import token_hex
from unittest.mock import patch
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

import grpc
import pytest

from pagekeeper.config import AppConfig
from pagekeeper.protos import pagekeeper_pb2_grpc
from pagekeeper.server import PageKeeperService
from pagekeeper.helpers import initialize_database


@pytest.fixture
def grpc_server(database, config):
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    pagekeeper_pb2_grpc.add_PageKeeperServicer_to_server(PageKeeperService(database, config), server)
    port = server.add_insecure_port('[::]:0')
    server.start()

    yield f'localhost:{port}'

    server.stop(0)


@pytest.fixture
def grpc_channel(grpc_server):
    return grpc.insecure_channel(grpc_server)


@pytest.fixture
def stub(grpc_channel):
    return pagekeeper_pb2_grpc.PageKeeperStub(grpc_channel)


@pytest.fixture
def database(config):
    db = initialize_database(url=config.MONGODB_URL, db_name=config.DATABASE_NAME)

    db.users.delete_many({})

    yield db

    db.users.delete_many({})
    db.client.drop_database(db)
    db.client.close()


@pytest.fixture(scope='session')
def config() -> None:
    return AppConfig()


@pytest.fixture(autouse=True, scope='session')
def _set_env() -> Generator[None, None, None]:
    with patch.dict(
        'os.environ',
        {
            'PAGEKEEPER_MONGODB_URL': 'mongodb://localhost:27017',
            'PAGEKEEPER_DATABASE_NAME': f'db_{token_hex(16)}',
            'PAGEKEEPER_SECRET_KEY': 'test_secret_key',
        },
        clear=True,
    ):
        yield
