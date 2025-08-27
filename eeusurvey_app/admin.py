# admin.py
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminSplitDateTime
from .models import Survey, Question, QuestionOption, QuestionCategory

# class SurveyAdminForm(forms.ModelForm):
#     class Meta:
#         model = Survey
#         fields = '__all__'
#         widgets = {
#             'start_time':AdminSplitDateTime(),
#             'end_time':AdminSplitDateTime()
#         }

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'version', 'language','is_active']
    list_filter = ['language','version']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'question_type', 'category']
    list_filter = ['question_type', 'category']

@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['question', 'label', 'text', 'is_other']

@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'survey']
