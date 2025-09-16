from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminSplitDateTime
from django.urls import path, reverse
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count, Q, F, Max, Min
from django.http import HttpResponse, JsonResponse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from collections import defaultdict
import csv
import json
from datetime import datetime, timedelta

from .models import (
    Answer, KeyChoice, Survey, Question, QuestionOption, 
    QuestionCategory, SurveyResponse
)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['question_text', 'question_type', 'category', 'placeholder', 'scale','required']
    readonly_fields = ['question_label']


class QuestionCategoryInline(admin.TabularInline):
    model = QuestionCategory
    extra = 0
    fields = ['cat_number', 'name']
    ordering = ['cat_number']


class KeyChoiceInline(admin.TabularInline):
    model = KeyChoice
    extra = 0
    fields = ['key', 'description']


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ['question', 'text_value', 'rating_value', 'number_value', 'custom_text']
    fields = ['question', 'text_value', 'rating_value', 'number_value', 'custom_text']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'version', 'language', 'is_active', 'response_count', 'date_range', 'analysis_link']
    list_filter = ['language', 'version', 'is_active', 'created_at']
    search_fields = ['title', 'instructions']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [KeyChoiceInline, QuestionCategoryInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'instructions', 'version', 'language')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time', 'is_active')
        }),
        ('System', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/analysis/',
                self.admin_site.admin_view(self.analysis_view),
                name='survey_analysis',
            ),
            path(
                '<path:object_id>/export/',
                self.admin_site.admin_view(self.export_responses),
                name='survey_export',
            ),
        ]
        return custom_urls + urls
    
    def response_count(self, obj):
        count = obj.responses.count()
        if count > 0:
            url = reverse('admin:eeusurvey_app_surveyresponse_changelist')
            return format_html('<a href="{}?survey__id__exact={}">{} responses</a>', url, obj.id, count)
        return '0 responses'
    response_count.short_description = 'Responses' # type: ignore
    
    def date_range(self, obj):
        return f"{obj.start_time} to {obj.end_time}"
    date_range.short_description = 'Active Period' # type: ignore
    
    def analysis_link(self, obj):
        if obj.responses.count() > 0:
            url = reverse('admin:survey_analysis', args=[obj.id])
            return format_html('<a href="{}" class="button">📊 View Analysis</a>', url)
        return 'No data'
    analysis_link.short_description = 'Analysis' # type: ignore
    
    def analysis_view(self, request, object_id):
        survey = get_object_or_404(Survey, id=object_id)
        
        # Basic statistics
        total_responses = survey.responses.count() # type: ignore
        
        if total_responses == 0:
            context = {
                'survey': survey,
                'total_responses': 0,
                'has_responses': False
            }
            return render(request, 'admin/survey_analysis.html', context)
        
        # Response timeline (last 30 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        daily_responses = (
            survey.responses # type: ignore
            .filter(submitted_at__date__gte=start_date)
            .extra({'date': "DATE(submitted_at)"})
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        # Question analysis
        questions_data = []
        for question in survey.questions.all().select_related('category'): # type: ignore
            question_data = self.analyze_question(question)
            questions_data.append(question_data)
        
        # Category summary
        category_summary = {}
        for category in survey.categories.all():             # type: ignore
                # Get all questions in this category
            category_questions = category.questions.all()
            total_questions = category_questions.count()

            # Count total answers across all questions in category
            total_answers = sum(q.answers.count() for q in category_questions)

            # Calculate average responses per question
            avg_responses = total_answers / total_questions if total_questions > 0 else 0

            category_summary[category.name] = {
                'total_questions': total_questions,
                'avg_responses': avg_responses
            }
        
        context = {
            'survey': survey,
            'total_responses': total_responses,
            'has_responses': True,
            'daily_responses': list(daily_responses),
            'questions_data': questions_data,
            'category_summary': category_summary,
            'completion_rate': (total_responses / max(survey.questions.count(), 1)) * 100 # type: ignore
        }
        
        return render(request, 'admin/survey_analysis.html', context)
    
    def analyze_question(self, question):
        """Analyze individual question responses"""
        answers = question.answers.all()
        total_answers = answers.count()
        
        analysis = {
            'question': question,
            'total_responses': total_answers,
            'response_rate': (total_answers / max(question.survey.responses.count(), 1)) * 100
        }
        
        if total_answers == 0:
            return analysis
        
        if question.question_type in ['single_choice', 'drop_down']:
            # Choice distribution
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
            option_counts = defaultdict(int)
            for answer in answers:
                for option in answer.selected_options.all():
                    option_counts[option.label or option.text or option.value] += 1
            analysis['distribution'] = dict(option_counts)
            
        elif question.question_type == 'rating':
            ratings = [a.rating_value for a in answers if a.rating_value is not None]
            if ratings:
                analysis['average_rating'] = sum(ratings) / len(ratings)
                analysis['rating_distribution'] = {
                    str(i): ratings.count(i) for i in range(1, 6)
                }
                
        elif question.question_type == 'number':
            numbers = [a.number_value for a in answers if a.number_value is not None]
            if numbers:
                analysis['average'] = sum(numbers) / len(numbers)
                analysis['min_value'] = min(numbers)
                analysis['max_value'] = max(numbers)
                
        elif question.question_type in ['text', 'text_area']:
            text_responses = [a.text_value for a in answers if a.text_value]
            analysis['text_count'] = len(text_responses)
            analysis['avg_length'] = sum(len(text) for text in text_responses) / len(text_responses) if text_responses else 0
            analysis['sample_responses'] = text_responses[:3]  # Show first 3 responses
        
        return analysis
    
    def export_responses(self, request, object_id):
        survey = get_object_or_404(Survey, id=object_id)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{survey.title}_responses.csv"'
        
        writer = csv.writer(response)
        
        # Header row
        headers = ['Response ID', 'Submitted At']
        questions = list(survey.questions.all().order_by('category__cat_number', 'id')) # type: ignore
        for question in questions:
            headers.append(f"Q{question.id}: {question.question_text[:50]}")
        writer.writerow(headers)
        
        # Data rows
        for survey_response in survey.responses.all(): # type: ignore
            row = [str(survey_response.id), survey_response.submitted_at.strftime('%Y-%m-%d %H:%M:%S')]
            
            for question in questions:
                try:
                    answer = Answer.objects.get(response=survey_response, question=question)
                    
                    if question.question_type in ['single_choice', 'drop_down', 'multi_select']:
                        selected_options = answer.selected_options.all()
                        if selected_options:
                            option_texts = [opt.label or opt.text or opt.value for opt in selected_options]
                            cell_value = '; '.join(option_texts)
                            if answer.custom_text:
                                cell_value += f" (Other: {answer.custom_text})"
                        else:
                            cell_value = ''
                    elif question.question_type == 'rating':
                        cell_value = answer.rating_value or ''
                    elif question.question_type == 'number':
                        cell_value = answer.number_value or ''
                    else:  # text, text_area
                        cell_value = answer.text_value or ''
                        
                    row.append(cell_value)
                except Answer.DoesNotExist:
                    row.append('')  # No answer for this question
            
            writer.writerow(row)
        
        return response


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'question_type', 'category', 'survey', 'response_count','required']
    list_filter = ['survey', 'question_type', 'category','required']
    search_fields = ['question_text']
    readonly_fields = ['question_label']
    
    def question_text_short(self, obj):
        return obj.question_text[:80] + "..." if len(obj.question_text) > 80 else obj.question_text
    question_text_short.short_description = 'Question Text' # type: ignore
    
    def response_count(self, obj):
        count = obj.answers.count()
        return f"{count} responses"
    response_count.short_description = 'Responses' # type: ignore


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['survey', 'label_or_text', 'value', 'is_other', 'usage_count']
    list_filter = ['survey', 'is_other']
    search_fields = ['label', 'text', 'value']
    
    def label_or_text(self, obj):
        return obj.label or obj.text or obj.value or f"Option {obj.id}"
    label_or_text.short_description = 'Option Text' # type: ignore
    
    def usage_count(self, obj):
        count = obj.questions.count()
        return f"Used in {count} questions"
    usage_count.short_description = 'Usage' # type: ignore


@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ['cat_number', 'name', 'survey', 'question_count']
    list_filter = ['survey']
    search_fields = ['name']
    ordering = ['survey', 'cat_number']
    
    def question_count(self, obj):
        count = obj.questions.count()
        return f"{count} questions"
    question_count.short_description = 'Questions' # type: ignore


@admin.register(KeyChoice)
class KeyChoiceAdmin(admin.ModelAdmin):
    list_display = ['key', 'description', 'survey']
    list_filter = ['survey']
    search_fields = ['key', 'description']


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['survey', 'submitted_at', 'ip_address', 'is_complete', 'answer_count']
    list_filter = ['survey', 'submitted_at', 'is_complete']
    readonly_fields = ['id', 'submitted_at', 'ip_address', 'user_agent']
    search_fields = ['survey__title', 'ip_address']
    inlines = [AnswerInline]
    
    fieldsets = (
        ('Response Info', {
            'fields': ('id', 'survey', 'is_complete', 'submitted_at')
        }),
        ('Respondent Details', {
            'fields': ('ip_address', 'user_agent', 'session_id'),
            'classes': ('collapse',)
        })
    )
    
    def answer_count(self, obj):
        count = obj.answers.count()
        total_questions = obj.survey.questions.count()
        return f"{count}/{total_questions} answered"
    answer_count.short_description = 'Completion' # type: ignore


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['response', 'question_short', 'answer_preview', 'created_at']
    list_filter = ['response__survey', 'question__question_type', 'created_at']
    search_fields = ['question__question_text', 'text_value']
    readonly_fields = ['created_at']
    
    def question_short(self, obj):
        return obj.question.question_text[:50] + "..." if len(obj.question.question_text) > 50 else obj.question.question_text
    question_short.short_description = 'Question' # type: ignore
    
    def answer_preview(self, obj):
        if obj.selected_options.exists():
            options = [opt.label or opt.text or opt.value for opt in obj.selected_options.all()]
            preview = '; '.join(options)
            if obj.custom_text:
                preview += f" (Other: {obj.custom_text[:30]}...)"
        elif obj.text_value:
            preview = obj.text_value[:50] + "..." if len(obj.text_value) > 50 else obj.text_value
        elif obj.rating_value:
            preview = f"Rating: {obj.rating_value}"
        elif obj.number_value:
            preview = f"Number: {obj.number_value}"
        else:
            preview = "No answer"
        return preview
    answer_preview.short_description = 'Answer' # type: ignore


# Custom Admin Site with Amharic interface
class SurveyAdminSite(admin.AdminSite):
    site_header = "የኢትዮጵያ ኤሌክትሪክ አገልግሎት ደንበኞች እርካታ ጥናት"
    site_title = "አገልግሎት እርካታ ጥናት"
    index_title = "ዳሽቦርድ"
    
    def get_urls(self): # type: ignore
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom dashboard with survey statistics"""
        # Overall statistics
        total_surveys = Survey.objects.count()
        active_surveys = Survey.objects.filter(is_active=True).count()
        total_responses = SurveyResponse.objects.count()
        
        # Recent activity
        recent_responses = SurveyResponse.objects.select_related('survey')[:10]
        recent_surveys = Survey.objects.order_by('-created_at')[:5]
        
        # Response statistics by survey
        survey_stats = []
        for survey in Survey.objects.filter(is_active=True):
            response_count = survey.responses.count() # type: ignore
            survey_stats.append({
                'survey': survey,
                'response_count': response_count,
                'completion_rate': (response_count / max(survey.questions.count(), 1)) * 100 # type: ignore
            })
        
        context = {
            'title': 'Survey Dashboard',
            'total_surveys': total_surveys,
            'active_surveys': active_surveys,
            'total_responses': total_responses,
            'recent_responses': recent_responses,
            'recent_surveys': recent_surveys,
            'survey_stats': survey_stats,
        }
        
        return render(request, 'admin/dashboard.html', context)


# Use custom admin site
admin_site = SurveyAdminSite(name='survey_admin')

# Register models with custom admin site
admin_site.register(Survey, SurveyAdmin)
admin_site.register(Question, QuestionAdmin)
admin_site.register(QuestionOption, QuestionOptionAdmin)
admin_site.register(QuestionCategory, QuestionCategoryAdmin)
admin_site.register(KeyChoice, KeyChoiceAdmin)
admin_site.register(SurveyResponse, SurveyResponseAdmin)
admin_site.register(Answer, AnswerAdmin)