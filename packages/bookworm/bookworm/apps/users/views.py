from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from pagekeeper import AuthenticateRequest

from bookworm.common.responses import success_response
from bookworm.common.authentication import init_authentication_service
from bookworm.apps.users.serializers import UserLoginSerializer, UserEnrollmentSerializer


class UserEnrollmentAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserEnrollmentSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.save()
        return success_response(data=user_id, status_code=status.HTTP_201_CREATED)


class UserLoginAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_service = init_authentication_service()
        response = auth_service.Authenticate(
            AuthenticateRequest(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
            )
        )

        return success_response(
            data={
                'access_token': response.access_token,
                'user': {
                    'is_admin': False,
                    'id': response.user.id,
                    'email': response.user.email,
                    'first_name': response.user.first_name,
                    'last_name': response.user.last_name,
                },
            },
            status_code=status.HTTP_200_OK,
        )
