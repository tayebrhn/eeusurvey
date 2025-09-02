# views.py
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import QuerySet
from .serializers import SurveySerializer
from .models import Survey, Question, QuestionOption, QuestionCategory

class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminUser()]  # 👈 Only admins
        return [AllowAny()]

    def create(self, request):
        """Create a new survey from JSON data"""
        try:
            data = request.data
            survey_data = data.get('metadata', {})

            start_str = survey_data.get('start', datetime.today().strftime('%Y-%m-%d'))
            end_str = survey_data.get('end', datetime.today().strftime('%Y-%m-%d'))

            survey = Survey.objects.create(
                title=survey_data.get('title', ''),
                instructions=survey_data.get('instructions', ''),
                version=survey_data.get('version', '1.0'),
                start_time = timezone.make_aware(datetime.strptime(start_str, '%Y-%m-%d')).date(),
                end_time = timezone.make_aware(datetime.strptime(end_str, '%Y-%m-%d') + timedelta(days=1, seconds=-1)).date(),
                language=survey_data.get('language', '')
            )

            # Create categories
            categories_map = {}
            for cat_data in data.get('question_categories', []):
                category = QuestionCategory.objects.create(
                    survey=survey,
                    name=cat_data.get('name', f"Category {cat_data.get('id', '')}")
                )
                categories_map[cat_data.get('id')] = category

            # Create questions & options
            for q_data in data.get('questions', []):
                category_id = q_data.get('category')
                category = categories_map.get(category_id)

                question = Question.objects.create(
                    survey=survey,
                    question_type=q_data.get('type'),
                    question_text=q_data.get('question'),
                    # question_label=q_data.get('label'),
                    category=category,
                    scale=q_data.get('scale'),
                    placeholder=q_data.get('placeholder')
                )

                for option in q_data.get('options', []):
                    if isinstance(option, dict):
                        QuestionOption.objects.create(
                            question=question,
                            value=option.get('value'),
                            label=option.get('label'),
                            text=option.get('text'),
                            is_other=option.get('is_other', False),
                        )
                    elif isinstance(option, str):
                        QuestionOption.objects.create(question=question, label=option)

            serializer = self.get_serializer(survey)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # @action(detail=True, methods=['get'])
    # def export_json(self, request, pk=None):
    #     """Export survey in original JSON-like format"""
    #     survey = self.get_object()
    #     print('EXPORT_METHOD',survey)
    #     serializer = self.get_serializer(survey)
    #     return Response(serializer.data)

# distinction b/n django and drf views
    # def list(self,request, *args,**kwargs):
    #     lang = request.query_params.get('lang')
    #     show_all = request.query_params.get('show_all')
    #     queryset = Survey.objects.all()
    #     if show_all == 'false':
    #         queryset = Survey.objects.filter(is_active=True)
    #     else:
    #         queryset = queryset.all()
    #     if lang:
    #         queryset = queryset.filter(language__iexact=lang)
    #     else:
    #         queryset = queryset.all()

    #     serializer = self.get_serializer(queryset,many=True)        
    #     return Response(serializer.data)

    # @action(detail=False, methods=['get'], url_path=r'lang/(?P<language>[^/]+)')
    # def list_by_language(self, request, language=None):
    #     """Return all active surveys in a given language"""
    #     queryset = Survey.objects.filter(language=language, is_active=True)
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)
    
    # @action(detail=False, methods=['get'], url_path=r'/(?P<language>[^/]+)')
    # def list_by_language(self, request, language=None):
    #     """Return surveys filtered by language (and active unless show_all=true)"""
    #     show_all = request.query_params.get('show_all')
    #     if show_all == 'true':
    #         queryset = Survey.objects.filter(language__iexact=language)
    #     else:
    #         queryset = Survey.objects.filter(language__iexact=language, is_active=True)
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)
    
    # @action(detail=True, methods=['get'], url_path=r'lang/(?P<language>[^/]+)')
    # def retrieve_by_language(self, request, pk=None, language=None):
    #     """Return a single survey by ID + language"""
    #     survey = get_object_or_404(Survey, pk=pk, language=language,is_active=True)
    #     serializer = self.get_serializer(survey)
    #     return Response(serializer.data)

    # @action(detail=True, methods=['get'], url_path=r'/')
    # def retrieve_by_language(self, request, pk=None, language=None):
    #     """Return one survey by id + language"""
    #     survey = get_object_or_404(Survey, pk=pk, language__iexact=language,is_active=True)
    #     serializer = self.get_serializer(survey)
    #     return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        lang = request.query_params.get("lang")
        show_all = request.query_params.get("show_all")

        queryset = Survey.objects.all()

        if show_all != "true":
            queryset = queryset.filter(is_active=True)

        if lang:
            queryset = queryset.filter(language=lang)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()  # single Survey by ID
        # lang = request.query_params.get("lang")

        # if lang and instance.language != lang:
        #     return Response(
        #         {"detail": "Survey not available in this language."}, status=404
        #     )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
