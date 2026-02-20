from django.contrib import admin
from django.urls import path, include
from django.conf.urls import handler404, handler500
from api_services.custom_exceptions import CustomException

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.urls")),
    path("api/users/", include("users.urls")),
]

handler404 = CustomException.custom_404_view
handler500 = CustomException.custom_500_view
