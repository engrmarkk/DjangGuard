# from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from django.http import JsonResponse
from api_services.logger import logger


class GlobalRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info("GlobalRateLimitMiddleware called")
        ip = self.get_client_ip(request)
        if request.user.is_authenticated:
            rate = "100/h"
            key_func = self.get_user_id_key
            limit_type = "authenticated"
        else:
            rate = "100/h"
            key_func = self.get_ip_key
            limit_type = "unauthenticated"

        try:
            from django_ratelimit.core import is_ratelimited

            limited = is_ratelimited(
                request=request,
                group="global_rate_limit",
                rate=rate,
                key=key_func,
                method="ALL",
                increment=True,
            )
            if limited:
                logger.warning(
                    f"Rate limit exceeded for {limit_type}: {ip if limit_type == 'unauthenticated' else request.user.id}"
                )
                raise Ratelimited()

            response = self.get_response(request)

            # Add rate limit headers
            response["X-RateLimit-Limit"] = rate
            response["X-RateLimit-Type"] = limit_type

            return response
        except Ratelimited:
            return JsonResponse(
                {"detail": "Rate limit exceeded. Please try again later."},
                status=429,
                headers={
                    "Retry-After": "3600",
                    "X-RateLimit-Limit": rate,
                    "X-RateLimit-Type": limit_type,
                },
            )

    # noinspection PyMethodMayBeStatic
    def get_user_id_key(self, request):
        return str(request.user.id)

    def get_ip_key(self, request):
        return self.get_client_ip(request)

    # noinspection PyMethodMayBeStatic
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
