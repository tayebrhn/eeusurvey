from django.urls import path, include
from django.contrib import admin
from eeusurvey_app.admin import admin_site  # instead of default admin


urlpatterns = [
    # path('admin/', admin.site.urls),
    path('admin/', admin_site.urls),  # ← Uses your custom dashboard
    path("api/", include("eeusurvey_app.urls")),
]
