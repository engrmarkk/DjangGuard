from rest_framework.views import APIView
from api_services.const_response import returned_response
from .serializers import LoginSerializer, RegisterSerializer
from rest_framework import status

# noinspection PyUnresolvedReferences
from api_services.utils import get_tokens_for_user, get_serializer_error
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.utils import timezone


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
            user = serializer.validated_data.get("user")
            user_agent = serializer.validated_data.get("user_agent")

            token_dict: dict = get_tokens_for_user(user, {"user_agent": user_agent})
            # returned_response(status_msg: str, message: str, status: int, data: dict|list = None)
            user.last_login = timezone.now()
            user.save()
            return returned_response(
                "success", "Login successful", status.HTTP_200_OK, token_dict
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
