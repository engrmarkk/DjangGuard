import uuid
from rest_framework_simplejwt.tokens import RefreshToken
from api_services.logger import logger


def hex_uuid():
    return str(uuid.uuid4().hex)


def get_tokens_for_user(user, data):
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    logger.info(f"create token data: {data}")

    for key, value in data.items():
        logger.info(f"create token: {key} - {value}")
        access[key] = value

    return {"refresh": str(refresh), "access": str(access)}


# get first serializer error
def get_serializer_error(serializer, default_message):
    return next((err[0] for err in serializer.errors.values() if err), default_message)
