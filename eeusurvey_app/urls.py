# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SurveyViewSet, get_survey_analysis, submit_survey_response
from .admin import admin_site  # instead of default admin

router = DefaultRouter()
router.register(r'surveys', SurveyViewSet)

urlpatterns = [
    path('surveys/<uuid:survey_id>/analysis/', get_survey_analysis, name='survey-analysis'),
    path('responses/submit/', submit_survey_response, name='submit-response'),
    path('', include(router.urls)),  # keeps /surveys/ and /surveys/<id>/
]
