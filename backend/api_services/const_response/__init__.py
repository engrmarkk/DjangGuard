from rest_framework.response import Response


def returned_response(
    status_msg: str, message: str, status: int, data: dict | list = None
):
    construct_dict = {"status": status_msg, "message": message}

    if data:
        construct_dict["data"]: dict | list = data

    return Response(construct_dict, status=status)
