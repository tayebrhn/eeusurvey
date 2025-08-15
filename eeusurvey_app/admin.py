# admin.py
from django.contrib import admin
from .models import Survey, Question, QuestionOption, QuestionCategory

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'version', 'language', 'created']
    list_filter = ['language', 'created']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_id', 'question_text', 'question_type', 'category']
    list_filter = ['question_type', 'category']

@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['question', 'label', 'text', 'is_other']

@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'survey']
