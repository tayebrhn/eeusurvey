# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.utils import timezone
from eeusurvey_app.analysis import analyze_survey_responses
from .serializers import SurveyResponseSerializer, SurveySerializer
from .models import Answer, KeyChoice, Survey, Question, QuestionOption, QuestionCategory, SurveyResponse
from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate
from collections import defaultdict
import json

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

            # Create KeyChoice
            # choice_map = {}
            for choice_data in data.get('key_choice', []):
                KeyChoice.objects.create(
                    survey=survey,
                    key=choice_data.get('key'),
                    description=choice_data.get('description')
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
                    category=category,
                    scale=q_data.get('scale'),
                    placeholder=q_data.get('placeholder'),
                    required=q_data.get('required',False) or False  
                )

                option_instances = []
                for option in q_data.get('options', []):
                    if isinstance(option, dict):
                        option_instance=QuestionOption.objects.create(
                            survey=survey,
                            value=option.get('value'),
                            label=option.get('label'),
                            text=option.get('text'),
                            is_other=option.get('is_other', False),
                        )
                        option_instances.append(option_instance)
                    elif isinstance(option, str):
                        option_instance=QuestionOption.objects.create(survey=survey, label=option)
                        option_instances.append(option_instance)
                question.options.add(*option_instances)
            serializer = self.get_serializer(survey)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()  # single Survey by ID
    #     # lang = request.query_params.get("lang")

    #     # if lang and instance.language != lang:
    #     #     return Response(
    #     #         {"detail": "Survey not available in this language."}, status=404
    #     #     )

    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)



@api_view(['POST'])
@permission_classes([AllowAny])
def submit_survey_response(request):
    """Submit a survey response"""
    try:
        data = request.data
        survey_id = data.get('survey_id')
        
        # Validate survey exists and is active
        try:
            survey = Survey.objects.get(id=survey_id, is_active=True)
        except Survey.DoesNotExist:
            return Response({'error': 'Survey not found or inactive'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Create response record
        survey_response = SurveyResponse.objects.create(
            survey=survey,
            ip_address=data.get('respondent_info', {}).get('ip_address'),
            user_agent=data.get('respondent_info', {}).get('user_agent'),
            session_id=data.get('respondent_info', {}).get('session_id'),
        )
        
        # Process each answer
        for response_data in data.get('responses', []):
            question_id = response_data.get('question_id')
            answer_data = response_data.get('answer', {})
            
            try:
                question = Question.objects.get(id=question_id, survey=survey)
            except Question.DoesNotExist:
                continue  # Skip invalid questions
            
            # Create answer record
            answer = Answer.objects.create(
                response=survey_response,
                question=question,
                text_value=answer_data.get('text_value'),
                rating_value=answer_data.get('rating_value'),
                number_value=answer_data.get('number_value'),
                custom_text=answer_data.get('text_value') if answer_data.get('is_other') else None
            )
            
            # Handle selected options
            if answer_data.get('selected_option_id'):
                try:
                    option = QuestionOption.objects.get(id=answer_data['selected_option_id'])
                    answer.selected_options.add(option)
                except QuestionOption.DoesNotExist:
                    pass
            
            if answer_data.get('selected_option_ids'):
                for option_id in answer_data['selected_option_ids']:
                    try:
                        option = QuestionOption.objects.get(id=option_id)
                        answer.selected_options.add(option)
                    except QuestionOption.DoesNotExist:
                        continue
        
        return Response({
            'success': True,
            'response_id': survey_response.id,
            'message': 'Response submitted successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_survey_analysis(request, survey_id):
    """Get comprehensive analysis of survey responses"""
    try:
        survey = Survey.objects.get(id=survey_id)
    except Survey.DoesNotExist:
        return Response({'error': 'Survey not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Basic statistics
    total_responses = SurveyResponse.objects.filter(survey=survey).count()
    
    if total_responses == 0:
        return Response({
            'survey': {
                'id': survey.id,
                'title': survey.title,
                'total_responses': 0
            },
            'analysis': {},
            'message': 'No responses yet'
        })
    
    # Response timeline
    daily_responses = (
        SurveyResponse.objects
        .filter(survey=survey)
        .extra({'date': "DATE(submitted_at)"})
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    
    # Analyze each question
    questions_analysis = {}
    
    for question in survey.questions.all():
        question_analysis = analyze_question(question)
        questions_analysis[question.id] = question_analysis
    
    # Category analysis
    category_analysis = {}
    for category in survey.categories.all():
        category_questions = category.questions.all()
        category_analysis[category.id] = {
            'name': category.name,
            'total_questions': category_questions.count(),
            'questions': [q.id for q in category_questions]
        }
    
    return Response({
        'survey': {
            'id': survey.id,
            'title': survey.title,
            'total_responses': total_responses,
            'response_timeline': list(daily_responses)
        },
        'categories': category_analysis,
        'questions': questions_analysis,
        'generated_at': timezone.now().isoformat()
    })


def analyze_question(question):
    """Analyze individual question responses"""
    answers = Answer.objects.filter(question=question)
    total_answers = answers.count()
    
    analysis = {
        'question_id': question.id,
        'question_text': question.question_text,
        'question_type': question.question_type,
        'total_responses': total_answers,
        'category': {
            'id': question.category.id,
            'name': question.category.name
        }
    }
    
    if total_answers == 0:
        return analysis
    
    if question.question_type in ['single_choice', 'drop_down']:
        # Analyze choice distribution
        option_counts = defaultdict(int)
        other_responses = []
        
        for answer in answers:
            selected_options = answer.selected_options.all()
            if selected_options:
                for option in selected_options:
                    if option.is_other and answer.custom_text:
                        other_responses.append(answer.custom_text)
                    option_counts[option.label or option.text or option.value] += 1
        
        analysis['distribution'] = dict(option_counts)
        analysis['other_responses'] = other_responses
        
    elif question.question_type == 'multi_select':
        # Analyze multiple selection patterns
        option_counts = defaultdict(int)
        combination_counts = defaultdict(int)
        
        for answer in answers:
            selected_options = answer.selected_options.all()
            if selected_options:
                # Count individual options
                option_labels = []
                for option in selected_options:
                    label = option.label or option.text or option.value
                    option_counts[label] += 1
                    option_labels.append(label)
                
                # Count combinations
                combination = ', '.join(sorted(option_labels))
                combination_counts[combination] += 1
        
        analysis['option_distribution'] = dict(option_counts)
        analysis['combination_distribution'] = dict(combination_counts)
        
    elif question.question_type == 'rating':
        # Calculate rating statistics
        ratings = [a.rating_value for a in answers if a.rating_value is not None]
        if ratings:
            analysis['average_rating'] = sum(ratings) / len(ratings)
            analysis['rating_distribution'] = {
                str(i): ratings.count(i) for i in range(1, 6)  # Assuming 1-5 scale
            }
            analysis['total_ratings'] = len(ratings)
        
    elif question.question_type == 'number':
        # Calculate number statistics
        numbers = [a.number_value for a in answers if a.number_value is not None]
        if numbers:
            analysis['average'] = sum(numbers) / len(numbers)
            analysis['minimum'] = min(numbers)
            analysis['maximum'] = max(numbers)
            analysis['total_numeric_responses'] = len(numbers)
        
    elif question.question_type in ['text', 'text_area']:
        # Analyze text responses
        text_responses = [a.text_value for a in answers if a.text_value]
        analysis['total_text_responses'] = len(text_responses)
        analysis['average_length'] = sum(len(text) for text in text_responses) / len(text_responses) if text_responses else 0
        
        # You could add more text analysis here (sentiment, keywords, etc.)
        # analysis['sample_responses'] = text_responses[:5]  # First 5 responses as sample
    
    return analysis
