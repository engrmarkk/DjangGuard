from rest_framework.views import exception_handler
from api_services.const_response import returned_response
from api_services.logger import logger
from django_ratelimit.exceptions import Ratelimited
from rest_framework import status


def custom_exception_handler(exc, context):
    # Get the default response from DRF
    response = exception_handler(exc, context)
    logger.error(f"Exception: {str(exc)}")
    # logger.error(f"Response Data: {response.data}")
    if isinstance(exc, Ratelimited):
        return returned_response(
            "failed",
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            message="Slow down a bit!, You are making too many requests.",
        )

    if response is not None:
        # Replace DRF's default format with my own
        return returned_response(
            "failed",
            status=response.status_code,
            message=response.data.get("detail", "Something went wrong"),
        )

    return response
