from rest_framework.views import APIView
from api_services.const_response import returned_response
from rest_framework.permissions import IsAuthenticated
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework import status
from django.core.cache import cache
from api_services.logger import logger


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    # noinspection PyMethodMayBeStatic
    @method_decorator(
        [ratelimit(key="user", rate="4/m", method="GET", block=True)], name="get"
    )
    def get(self, request):
        user = request.user
        key = f"user_profile:{user.id}"
        user_dict = cache.get(key)
        if user_dict:
            logger.info("User profile retrieved from cache")
            return returned_response(
                "success",
                "User profile retrieved successfully",
                status.HTTP_200_OK,
                user_dict,
            )
        user_dict = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "date_joined": user.created_at,
        }
        cache.set(key, user_dict, timeout=60 * 60)
        return returned_response(
            "success",
            "User profile retrieved successfully",
            status.HTTP_200_OK,
            user_dict,
        )
