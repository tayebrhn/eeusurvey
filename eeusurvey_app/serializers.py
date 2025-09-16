# serializers.py
from rest_framework import serializers
from .models import KeyChoice, Survey, Question, QuestionOption, QuestionCategory,Answer,SurveyResponse

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
    # required = serializers.BooleanField(source='required')

    class Meta:
        model = Question
        fields = ['id', 'type', 'question','label', 'category', 'options', 'scale', 'placeholder','required']


class KeyChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyChoice
        fields = ['key','description']

class QuestionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCategory
        fields = ['id','cat_number', 'name']


class SurveySerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_categories = QuestionCategorySerializer(many=True, source='categories', read_only=True)
    key_choice = KeyChoiceSerializer(many=True,source='keys', read_only=True)
    metadata = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    # is_active = serializers.SerializerMethodField()
    # survey = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = ['id','metadata', 'questions','key_choice' ,'question_categories']
    
    # def get_id(self,obj):
    #     return obj.id
    def get_id(self,obj):
        return obj.id

    def get_metadata(self, obj):
        return {
            'title': obj.title,
            'instructions': obj.instructions,
            'start': obj.start_time.strftime('%Y-%m-%d'),
            'end': obj.end_time.strftime('%Y-%m-%d'),
            'version': obj.version,
            'language': obj.language,
        }

class AnswerSerializer(serializers.ModelSerializer):
    selected_option_ids = serializers.SerializerMethodField()
    
    class Meta:
        model = Answer
        fields = ['question', 'selected_option_ids', 'text_value', 'rating_value', 
                 'number_value', 'custom_text']
    
    def get_selected_option_ids(self, obj):
        return [option.id for option in obj.selected_options.all()]


class SurveyResponseSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = SurveyResponse
        fields = ['id', 'survey', 'submitted_at', 'answers', 'is_complete']

