# urls.py (app-level urls.py in surveys app)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SurveyViewSet
)

router = DefaultRouter()
router.register(r'surveys', SurveyViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    # Database admin URLs
    # path('admin/database/', database_admin, name='database_admin'),
    # path('admin/database/reset-data/', reset_data_only, name='reset_data_only'),
    # path('admin/database/reset-migrations/', reset_migrations, name='reset_migrations'),
    # path('admin/database/load-sample/', load_sample_data, name='load_sample_data'),
    # path('admin/database/stats/', database_stats, name='database_stats'),
]