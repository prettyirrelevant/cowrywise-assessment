import logging
from concurrent.futures import ThreadPoolExecutor

import grpc
from pymongo.errors import DuplicateKeyError
from pymongo.database import Database

from pagekeeper.config import AppConfig
from pagekeeper.protos import pagekeeper_pb2, pagekeeper_pb2_grpc
from pagekeeper.helpers import (
    create_token,
    verify_token,
    hash_password,
    verify_password,
    initialize_database,
    generate_user_identifier,
)

logger = logging.getLogger(__name__)


class PageKeeperService(pagekeeper_pb2_grpc.PageKeeperServicer):
    def __init__(self, database: Database, config: AppConfig):
        """Initialize the PageKeeperService."""
        self.database = database
        self.config = config

    def Register(
        self,
        request: pagekeeper_pb2.RegisterRequest,
        context: grpc.aio.ServicerContext,
    ) -> pagekeeper_pb2.RegisterResponse:
        """Register a new user."""
        identifier = generate_user_identifier()
        hashed_password = hash_password(request.password)

        try:
            self.database.users.insert_one(
                {
                    'email': request.email,
                    'user_id': identifier,
                    'is_admin': request.is_admin,
                    'last_name': request.last_name,
                    'first_name': request.first_name,
                    'hashed_password': hashed_password,
                }
            )
            return pagekeeper_pb2.RegisterResponse(message='registration successful', id=identifier)
        except DuplicateKeyError:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details('email address already in use')
            return pagekeeper_pb2.RegisterResponse()

    def Authenticate(
        self,
        request: pagekeeper_pb2.AuthenticateRequest,
        context: grpc.aio.ServicerContext,
    ) -> pagekeeper_pb2.AuthenticateResponse:
        """Authenticate a user and return an access token."""
        result = self.database.users.find_one({'email': request.email})
        if result is None:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('invalid credentials provided')
            return pagekeeper_pb2.AuthenticateResponse()

        is_valid_password = verify_password(expected_password=request.password, actual_hash=result['hashed_password'])
        if not is_valid_password:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('invalid credentials provided')
            return pagekeeper_pb2.AuthenticateResponse()

        access_token = create_token(
            user_id=result['user_id'],
            is_admin=result['is_admin'],
            secret=self.config.SECRET_KEY,
            expiration=self.config.ACCESS_TOKEN_EXPIRATION,
        )

        return pagekeeper_pb2.AuthenticateResponse(
            message='access token returned successfully',
            access_token=access_token,
            user=pagekeeper_pb2.User(
                id=result['user_id'],
                email=result['email'],
                is_admin=result['is_admin'],
                last_name=result['last_name'],
                first_name=result['first_name'],
            ),
        )

    def Verify(
        self,
        request: pagekeeper_pb2.VerifyRequest,
        context: grpc.aio.ServicerContext,
    ) -> pagekeeper_pb2.VerifyResponse:
        """Verify an access token and return user information."""
        payload = verify_token(token=request.access_token, secret=self.config.SECRET_KEY)
        if payload is None:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('access token is invalid')
            return pagekeeper_pb2.VerifyResponse()

        user = self.database.users.find_one({'user_id': payload['user_id']})
        if user is None:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details('access token is expired')
            return pagekeeper_pb2.VerifyResponse()

        return pagekeeper_pb2.VerifyResponse(
            message='successful verification',
            user=pagekeeper_pb2.User(
                id=user['user_id'],
                email=user['email'],
                is_admin=user['is_admin'],
                last_name=user['last_name'],
                first_name=user['first_name'],
            ),
        )

    def FetchUsers(
        self,
        request: pagekeeper_pb2.FetchUsersRequest,
        context: grpc.aio.ServicerContext,
    ) -> pagekeeper_pb2.FetchUsersResponse:
        """Fetch users based on provided criteria."""
        query = {}
        page = request.page if request.page > 0 else 1
        page_size = request.page_size if request.page_size > 0 else 50
        if request.ids:
            query = {'user_id': {'$in': list(request.ids)}}
            page_size = len(request.ids)
            page = 1

        skip = (page - 1) * page_size
        total_users = self.database.users.count_documents(query)
        user_entries = self.database.users.find(query).skip(skip).limit(page_size)

        users = [
            pagekeeper_pb2.User(
                id=entry['user_id'],
                email=entry['email'],
                is_admin=entry['is_admin'],
                last_name=entry['last_name'],
                first_name=entry['first_name'],
            )
            for entry in user_entries
        ]

        return pagekeeper_pb2.FetchUsersResponse(
            message='users fetched successfully',
            users=users,
            total_users=total_users,
            current_page=page,
        )


def serve() -> None:
    """Start the gRPC server."""
    config = AppConfig()
    database = initialize_database(url=config.MONGODB_URL, db_name=config.DATABASE_NAME)

    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    pagekeeper_pb2_grpc.add_PageKeeperServicer_to_server(PageKeeperService(database, config), server)
    server.add_insecure_port(f'[::]:{config.PORT}')

    logger.debug('starting server on [::]:%s', config.PORT)

    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logger.debug('starting server...')
    serve()
