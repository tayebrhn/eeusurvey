# serializers.py
from rest_framework import serializers
from .models import Survey, Question, QuestionOption, QuestionCategory

class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'value', 'label', 'text', 'is_other']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {k: v for k, v in data.items() if v is not None}


class QuestionSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source='question_text')
    type = serializers.CharField(source='question_type')
    label = serializers.CharField(source='question_label')
    category = serializers.IntegerField(source='category.id')
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'type', 'question','label', 'category', 'options', 'scale', 'placeholder']


class QuestionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCategory
        fields = ['id', 'name']


class SurveySerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_categories = QuestionCategorySerializer(many=True, source='categories', read_only=True)
    metadata = serializers.SerializerMethodField()
    # survey = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = ['metadata', 'questions', 'question_categories']

    def get_metadata(self, obj):
        return {
            'title': obj.title,
            'instructions': obj.instructions,
            'start': obj.start_time.strftime('%Y-%m-%d'),
            'end': obj.end_time.strftime('%Y-%m-%d'),
            'version': obj.version,
            'language': obj.language,
        }

    # def get_survey(self, obj):
    #     return {
    #         'title': obj.title,
    #         'instructions': obj.instructions,
    #     }
