# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime
from .serializers import SurveySerializer
from .models import Survey, Question, QuestionOption, QuestionCategory

class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer

    def create(self, request):
        """Create a new survey from JSON data"""
        try:
            data = request.data
            survey_data = data.get('survey', {})
            
            # Create Survey
            survey = Survey.objects.create(
                title=survey_data.get('title', ''),
                instructions=survey_data.get('instructions', ''),
                version=survey_data.get('version', '1.0'),
                created=datetime.strptime(
                    survey_data.get('metadata', {}).get('created', '2025-08-12'), 
                    '%Y-%m-%d'
                ).date(),
                language=survey_data.get('metadata', {}).get('language', 'amharic')
            )

            # Create Question Categories
            categories = data.get('question_categories', [])
            for cat_data in categories:
                QuestionCategory.objects.create(
                    survey=survey,
                    name=cat_data.get('name', '')
                )

            # Create Questions and Options
            questions = data.get('questions', [])
            for q_data in questions:
                question = Question.objects.create(
                    survey=survey,
                    question_id=q_data.get('id'),
                    question_type=q_data.get('type'),
                    question_text=q_data.get('question'),
                    category=q_data.get('category', ''),
                    scale=q_data.get('scale'),
                    placeholder=q_data.get('placeholder')
                )

                # Handle different option formats
                options = q_data.get('options', [])
                if isinstance(options, list):
                    for i, option in enumerate(options):
                        if isinstance(option, dict):
                            # Handle object format
                            QuestionOption.objects.create(
                                question=question,
                                option_id=option.get('id'),
                                value=option.get('value'),
                                label=option.get('label'),
                                text=option.get('text'),
                                is_other=option.get('is_other', False)
                            )
                        elif isinstance(option, str):
                            # Handle string format
                            QuestionOption.objects.create(
                                question=question,
                                label=option
                            )

            serializer = self.get_serializer(survey)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def export_json(self, request, pk=None):
        """Export survey in the exact original JSON format"""
        survey = self.get_object()
        serializer = self.get_serializer(survey)
        return Response(serializer.data)
