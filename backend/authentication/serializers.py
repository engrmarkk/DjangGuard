from django.contrib.auth import authenticate
from django.contrib.auth.signals import user_logged_in
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from .models import User, UserLoginRecord
from django.contrib.auth.password_validation import validate_password
from api_services.logger import logger


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, trim_whitespace=True)
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        request = self.context.get("request")

        if email and password:
            # Authenticate using email as the username
            user = authenticate(request=request, username=email, password=password)

            if not user:
                # This triggers django-axes if attempts fail
                raise AuthenticationFailed("Invalid email or password.")

            if not user.is_active:
                raise AuthenticationFailed("User account is disabled.")

            # EXTREMELY IMPORTANT: Fire the signal for your security alerts
            user_logged_in.send(sender=user.__class__, request=request, user=user)
            # get the recent login record to access the user_agent
            login_record = (
                UserLoginRecord.objects.filter(user=user)
                .order_by("-created_at")
                .first()
            )
            logger.info(f"login record: {login_record.user_agent}")
            attrs["user"] = user
            attrs["user_agent"] = (
                login_record.user_agent
                if login_record
                else request.META.get("HTTP_USER_AGENT", "")
            )
            return attrs

        raise serializers.ValidationError(
            {"detail": "Both 'email' and 'password' are required."}
        )


# register serializer
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, trim_whitespace=True)
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, trim_whitespace=False
    )
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}, trim_whitespace=False
    )
    first_name = serializers.CharField(write_only=True, trim_whitespace=True)
    last_name = serializers.CharField(write_only=True, trim_whitespace=True)

    def create(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")
        first_name = attrs.get("first_name")
        last_name = attrs.get("last_name")

        if email and password and password_confirm and first_name and last_name:
            if password != password_confirm:
                raise serializers.ValidationError({"detail": "Passwords do not match."})
            validate_password(password)
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    {"detail": "User with this email already exists."}
                )

            attrs["user"] = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            return attrs

        raise serializers.ValidationError({"detail": "All fields are required."})
