import grpc

from django.conf import settings

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from pagekeeper import VerifyRequest, PageKeeperStub


class CustomUser:
    def __init__(self, user_proto):
        self.is_active = True
        self.id = user_proto.id
        self.is_authenticated = True
        self.email = user_proto.email
        self.is_admin = user_proto.is_admin
        self.last_name = user_proto.last_name
        self.first_name = user_proto.first_name

    @property
    def is_anonymous(self):
        return False


class JWTAuthentication(BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise AuthenticationFailed(msg)

        if len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError as e:
            msg = 'Invalid token header. Token string should not contain invalid characters.'
            raise AuthenticationFailed(msg) from e

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        auth_service = init_authentication_service()

        try:
            response = auth_service.Verify(VerifyRequest(access_token=key))
            user = CustomUser(response.user)
        except grpc.RpcError as e:
            raise AuthenticationFailed(e.details) from e

        return (user, None)


def init_authentication_service():
    channel = grpc.insecure_channel(settings.AUTHENTICATION_SERVER_URL)
    return PageKeeperStub(channel)
