import jwt
from django.http import JsonResponse
from django.conf import settings
from rest_framework import status
from api_services.logger import logger
from django.contrib.auth import get_user_model

User = get_user_model()


class UserAgentValidationMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get authorization header
        auth_header = request.META.get("HTTP_AUTHORIZATION")

        if auth_header:
            # Validate token format
            token = self.extract_token(auth_header)
            if not token:
                return JsonResponse(
                    {"detail": "Invalid token format"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Validate user agent
            validation_result = self.validate_user_agent(token, request)
            if validation_result is not True:
                return validation_result

        return self.get_response(request)

    # noinspection PyMethodMayBeStatic
    def extract_token(self, auth_header):
        """Extract and validate JWT token from Authorization header"""
        try:
            if not auth_header.startswith("Bearer "):
                return None

            parts = auth_header.split()
            if len(parts) != 2:
                return None

            return parts[1]
        except Exception as e:
            logger.error(f"Error extracting token: {str(e)}")
            return None

    # noinspection PyMethodMayBeStatic
    def validate_user_agent(self, token, request):
        """Validate that token's user agent matches request's user agent"""
        try:
            # Decode token without verification first to get claims
            # This doesn't verify signature, just extracts payload
            unverified_payload = jwt.decode(token, options={"verify_signature": False})

            logger.info(f"unverified_payload: {unverified_payload}")

            # Get user agent from token claims
            token_user_agent = unverified_payload.get("user_agent")

            # Get current request user agent
            current_user_agent = request.META.get("HTTP_USER_AGENT", "")

            # Log for debugging (optional)
            logger.info(
                f"Token UA: {token_user_agent}, Request UA: {current_user_agent}"
            )

            # If token has user_agent claim but it doesn't match
            if token_user_agent != current_user_agent:
                logger.warning(
                    f"User agent mismatch! Token: {token_user_agent}, "
                    f"Request: {current_user_agent}, Path: {request.path}"
                )
                return JsonResponse(
                    {
                        "detail": "User agent mismatch",
                        "message": "Token was issued for a different device/browser",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Optional: Add decoded token to request for later use
            try:
                # Now verify the token properly
                validated_payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=["HS256"]
                )
                request.jwt_payload = validated_payload
                user_id = validated_payload.get("user_id")
                logger.info("user_id was used")

                user = User.objects.get(id=user_id)
                if not user.is_active:
                    return JsonResponse(
                        {"detail": "User is not active"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            except jwt.ExpiredSignatureError:
                return JsonResponse(
                    {"detail": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED
                )
            except jwt.InvalidTokenError as e:
                return JsonResponse(
                    {"detail": f"Invalid token: {str(e)}"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            return True

        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token during UA validation: {str(e)}")
            return JsonResponse(
                {"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Unexpected error in user agent validation: {str(e)}")
            return JsonResponse(
                {"detail": "Authentication error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
