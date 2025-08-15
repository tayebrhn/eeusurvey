# serializers.py
from rest_framework import serializers
from .models import Survey, Question, QuestionOption, QuestionCategory

class QuestionOptionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='option_id', required=False, allow_null=True)
    
    class Meta:
        model = QuestionOption
        fields = ['id', 'value', 'label', 'text', 'is_other']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Remove None values to match original JSON structure
        return {k: v for k, v in data.items() if v is not None}

class QuestionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='question_id')
    question = serializers.CharField(source='question_text')
    type = serializers.CharField(source='question_type')
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'type', 'question', 'category', 'options', 'scale', 'placeholder']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Handle different option formats based on question type
        if instance.question_type == 'multi_select':
            # For multi_select, options should be a list of objects with value and label
            data['options'] = [
                {'value': opt.value, 'label': opt.label} 
                for opt in instance.options.all() if opt.value and opt.label
            ]
        elif instance.question_type == 'single_choice':
            if instance.options.exists():
                # Check if options have value/label structure or id/text structure
                first_option = instance.options.first()
                if first_option.value and first_option.label:
                    data['options'] = [opt.label for opt in instance.options.all()]
                else:
                    data['options'] = [
                        {
                            'id': opt.option_id,
                            'text': opt.text,
                            **({'is_other': True} if opt.is_other else {})
                        }
                        for opt in instance.options.all()
                    ]
        
        # Remove None values to match original JSON structure
        return {k: v for k, v in data.items() if v is not None}

class QuestionCategorySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    
    class Meta:
        model = QuestionCategory
        fields = ['id', 'name']

class SurveySerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_categories = QuestionCategorySerializer(many=True, source='categories', read_only=True)
    metadata = serializers.SerializerMethodField()
    survey = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = ['survey', 'questions', 'question_categories','metadata']

    def get_metadata(self, obj):
        return {
            'created': obj.created.strftime('%Y-%m-%d'),
            'language': obj.language
        }

    def get_survey(self, obj):
        return {
            'title': obj.title,
            'instructions': obj.instructions,
            'version': obj.version,
            'metadata': self.get_metadata(obj)
        }
