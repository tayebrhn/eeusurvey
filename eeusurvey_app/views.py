# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime
from .serializers import SurveySerializer
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.core.management import call_command
from django.contrib.auth.decorators import user_passes_test
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

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_superuser)
def database_admin(request):
    """Main database administration page"""
    context = {
        'survey_count': Survey.objects.count(),
        'question_count': Question.objects.count(),
        'option_count': QuestionOption.objects.count(),
        'category_count': QuestionCategory.objects.count(),
    }
    return render(request, 'surveys/database_admin.html', context)

@user_passes_test(is_superuser)
def reset_data_only(request):
    """Reset only the data, keep the database structure"""
    if request.method == 'POST':
        try:
            Survey.objects.all().delete()
            Question.objects.all().delete()
            QuestionOption.objects.all().delete()
            QuestionCategory.objects.all().delete()
            messages.success(request, 'All survey data has been deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting data: {str(e)}')
    
    return redirect('database_admin')

@user_passes_test(is_superuser)
def reset_migrations(request):
    """Reset migrations and recreate database structure"""
    if request.method == 'POST':
        try:
            # Clear data first
            Survey.objects.all().delete()
            Question.objects.all().delete()
            QuestionOption.objects.all().delete()
            QuestionCategory.objects.all().delete()
            
            # Run migrations
            call_command('migrate', 'surveys', 'zero', verbosity=0)
            call_command('migrate', 'surveys', verbosity=0)
            
            messages.success(request, 'Database structure has been reset successfully!')
        except Exception as e:
            messages.error(request, f'Error resetting migrations: {str(e)}')
    
    return redirect('database_admin')

@user_passes_test(is_superuser)
def load_sample_data(request):
    """Load the sample survey data"""
    if request.method == 'POST':
        try:
            # Sample data from your JSON
            sample_data = {
                "survey": {
                    "title": "የኢትዮጵያ ኤሌክትሪክ አገልግሎት ደንበኞች እርካታ ጥናት",
                    "instructions": "እባክዎ የድርጅቱን አገልግሎት በተሰጠው መለኪያ ይለይቱ።",
                    "version": "1.0",
                    "metadata": {
                        "created": "2025-08-12",
                        "language": "amharic"
                    }
                },
                "question_categories": [
                    {"id": 1, "name": "demographics"},
                    {"id": 2, "name": "service_location"},
                    {"id": 3, "name": "service"},
                    {"id": 4, "name": "billing"},
                    {"id": 5, "name": "technical"},
                ]
            }
            
            # Create survey
            from datetime import datetime
            survey = Survey.objects.create(
                title=sample_data['survey']['title'],
                instructions=sample_data['survey']['instructions'],
                version=sample_data['survey']['version'],
                created=datetime.strptime(sample_data['survey']['metadata']['created'], '%Y-%m-%d').date(),
                language=sample_data['survey']['metadata']['language']
            )
            
            # Create categories
            for cat_data in sample_data['question_categories']:
                QuestionCategory.objects.create(
                    survey=survey,
                    name=cat_data['name']
                )
            
            messages.success(request, 'Sample survey data loaded successfully!')
        except Exception as e:
            messages.error(request, f'Error loading sample data: {str(e)}')
    
    return redirect('database_admin')

@user_passes_test(is_superuser)
def database_stats(request):
    """Get database statistics as JSON"""
    stats = {
        'surveys': Survey.objects.count(),
        'questions': Question.objects.count(),
        'options': QuestionOption.objects.count(),
        'categories': QuestionCategory.objects.count(),
        'recent_surveys': list(Survey.objects.order_by('-created_at')[:5].values('id', 'title', 'created_at'))
    }
    return JsonResponse(stats)
