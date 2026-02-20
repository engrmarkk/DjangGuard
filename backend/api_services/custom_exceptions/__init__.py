from rest_framework import status
from django.http import JsonResponse
from api_services.logger import logger


class CustomException:
    @staticmethod
    def custom_404_view(request, exception=None):
        logger.exception(f"404 exception: {exception}")
        return JsonResponse(
            {
                "message": "Resource Not Found",
                "status": "failed",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    @staticmethod
    def custom_500_view(request, exception=None):
        logger.exception(f"500 exception: {exception}")
        return JsonResponse(
            {
                "message": "Network Error",
                "status": "failed",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
