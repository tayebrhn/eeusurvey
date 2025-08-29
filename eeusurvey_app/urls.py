# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SurveyViewSet

router = DefaultRouter()
router.register(r'surveys', SurveyViewSet)

survey_list_lang = SurveyViewSet.as_view({'get': 'list_by_language'})
survey_detail_lang = SurveyViewSet.as_view({'get': 'retrieve_by_language'})

urlpatterns = [
    path('surveys/<str:language>/', survey_list_lang, name='survey-list-lang'),
    path('surveys/<str:language>/<uuid:pk>/', survey_detail_lang, name='survey-detail-lang'),
    path('', include(router.urls)),  # keeps /surveys/ and /surveys/<id>/
]
