from rest_framework import serializers

from pagekeeper import RegisterRequest

from bookworm.common.authentication import init_authentication_service


class UserEnrollmentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    last_name = serializers.CharField()
    first_name = serializers.CharField()

    def create(self, validated_data):
        auth_service = init_authentication_service()
        response = auth_service.Register(
            RegisterRequest(
                is_admin=False,
                email=validated_data['email'],
                password=validated_data['password'],
                last_name=validated_data['last_name'],
                first_name=validated_data['first_name'],
            )
        )
        return response.id


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
