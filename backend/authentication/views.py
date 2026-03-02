from rest_framework.views import APIView
from api_services.const_response import returned_response
from .serializers import LoginSerializer, RegisterSerializer
from rest_framework import status
# noinspection PyUnresolvedReferences
from api_services.utils import get_tokens_for_user, get_serializer_error
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import jwt
from api_services.environmentals import SECRET_KEY
from api_services.redis_service import RedisService
from datetime import timedelta


# login view
# user the user email and ip to rate limit
@method_decorator(
    [
        ratelimit(key="post:email", rate="5/m", method="POST", block=True),
        ratelimit(key="ip", rate="10/m", method="POST", block=True),
    ],
    name="post",
)
class LoginView(APIView):
    # noinspection PyMethodMayBeStatic
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            redis_service = RedisService()
            user = serializer.validated_data.get("user")
            user_agent = serializer.validated_data.get("user_agent")

            token_dict: tuple = get_tokens_for_user(user, {"user_agent": user_agent})
            # returned_response(status_msg: str, message: str, status: int, data: dict|list = None)
            user.last_login = timezone.now()
            user.save()
            redis_service.set(user.id, token_dict[1], expire=timedelta(days=1))
            return returned_response(
                "success", "Login successful", status.HTTP_200_OK, token_dict[0]
            )
        return returned_response(
            "failed",
            get_serializer_error(serializer, "Login failed"),
            status.HTTP_400_BAD_REQUEST,
        )


# register view
# user the user email and ip to rate limit
@method_decorator(
    [
        ratelimit(key="post:email", rate="5/m", method="POST", block=True),
        ratelimit(key="ip", rate="10/m", method="POST", block=True),
    ],
    name="post",
)
class RegisterView(APIView):
    # noinspection PyMethodMayBeStatic
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return returned_response(
                "success", "User registered successfully", status.HTTP_201_CREATED
            )
        return returned_response(
            "failed",
            get_serializer_error(serializer, "User registration failed"),
            status.HTTP_400_BAD_REQUEST,
        )


# logout view
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    # noinspection PyMethodMayBeStatic
    def post(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")

        if not auth_header.startswith("Bearer "):
            return returned_response(
                "failed",
                "Invalid token format",
                status.HTTP_401_UNAUTHORIZED,
            )

        parts = auth_header.split()
        if len(parts) != 2:
            return returned_response(
                "failed",
                "Invalid token format.",
                status.HTTP_401_UNAUTHORIZED,
            )

        token = parts[1]
        try:
            # Decode and verify token
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            # Extract jti
            jti = payload.get("jti")
            redis_service = RedisService()
            redis_service.set(jti, "blacklisted", expire=timedelta(days=1))
            return returned_response(
                "success",
                "Logout successful",
                status.HTTP_200_OK,
            )
        except jwt.ExpiredSignatureError:
            return returned_response(
                "failed",
                "Token has expired",
                status.HTTP_401_UNAUTHORIZED,
            )
        except jwt.InvalidTokenError as e:
            return returned_response(
                "failed",
                f"Invalid token: {str(e)}",
                status.HTTP_401_UNAUTHORIZED,
            )
