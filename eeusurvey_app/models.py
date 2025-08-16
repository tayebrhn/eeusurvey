# models.py
from django.db import models

class Survey(models.Model):
    title = models.CharField(max_length=500)
    instructions = models.TextField()
    version = models.CharField(max_length=20)
    created = models.DateField()
    language = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class QuestionCategory(models.Model):
    name = models.CharField(max_length=100)
    survey = models.ForeignKey(Survey, related_name='categories', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Question(models.Model):
    QUESTION_TYPES = [
        ('single_choice', 'Single Choice'),
        ('multi_select', 'Multi Select'),
        ('rating', 'Rating'),
        ('number', 'Number'),
        ('text', 'Text'),
    ]

    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    question_id = models.IntegerField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    # category = models.CharField(max_length=100)
    category = models.ForeignKey(QuestionCategory,related_name="question",on_delete=models.CASCADE)
    scale = models.CharField(max_length=20, blank=True, null=True)
    placeholder = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        unique_together = ('survey', 'question_id')

    def __str__(self):
        return f"Q{self.question_id}: {self.question_text[:50]}"

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    option_id = models.IntegerField(blank=True, null=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=200)
    text = models.CharField(max_length=200, blank=True, null=True)
    is_other = models.BooleanField(default=False)

    def __str__(self): # type: ignore
        return self.label or self.text or self.value
