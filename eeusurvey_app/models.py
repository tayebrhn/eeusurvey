# models.py
import uuid
from django.utils import timezone
from django.db import models
    
class Survey(models.Model):
    LANGUAGES = [
        ("en","English"),
        ("am","Amharic"),
        ("om","Afan Oromo")
    ]
    # DEFAULT_KEYS = [
    #     ('1','እጅግ በጣም ጥሩ'),
    #     ('2', 'በጣም ጥሩ'),
    #     ('3', 'ጥሩ'),
    #     ('4', 'አጥጋቢ አይደለም'),
    #     ('5', 'በጣም አጥጋቢ አይደለም')
    # ]
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title = models.CharField(max_length=500)
    instructions = models.TextField()
    version = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    start_time = models.DateField()
    end_time = models.DateField()
    language = models.CharField(max_length=50,choices=LANGUAGES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self,*args,**kwargs):
        if self.end_time <= timezone.now().date():
            self.is_active = False
        super().save(*args,**kwargs)

    # @property
    # def has_expired(self):
    #     return timezone.now().date() >= self.end_time
    
    def __str__(self):
        return f"{self.title} ({'active' if self.is_active else 'inactive'})"


class QuestionCategory(models.Model):
    name = models.CharField(max_length=100)
    survey = models.ForeignKey(Survey, related_name='categories', on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    

class KeyChoice(models.Model):
    key = models.CharField(max_length=10)   # Editable key (e.g. "1", "2", ...)
    description = models.CharField(max_length=100)       # Editable label (e.g. "እጅግ በጣም ጥሩ")
    survey = models.ForeignKey(Survey, related_name='keys', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["survey","key"],name="unique_key_per_survey")
        ]

    def __str__(self):
        return f"{self.survey.title} | {self.key} - {self.description}"


class Question(models.Model):
    QUESTION_TYPES = [
        ('single_choice', 'Single Choice'),
        ('multi_select', 'Multi Select'),
        ('drop_down', 'Drop Down'),
        ('text_area', 'Text Area'),
        ('rating', 'Rating'),
        ('number', 'Number'),
        ('text', 'Text'),
    ]

    id = models.BigAutoField(primary_key=True,editable=False)
    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    category = models.ForeignKey(QuestionCategory, related_name="questions", on_delete=models.CASCADE)
    placeholder = models.CharField(max_length=200, blank=True, null=True)
    scale = models.CharField(max_length=20, blank=True, null=True)
    question_label = models.TextField(editable=False)
    
    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        if not self.question_label:
            self.question_label = f"Q_{self.id}"

            #save agian to update the label
            super().save(update_fields=['question_label'])

    class Meta:
        unique_together = ('survey', 'id')

    def __str__(self):
        return f"Q{self.question_text[:50]}"


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    id = models.BigAutoField(primary_key=True,editable=False)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=200, blank=True, null=True)
    text = models.CharField(max_length=200, blank=True, null=True)
    is_other = models.BooleanField(default=False)

    def __str__(self):
        return self.label or self.text or self.value or f"Option {self.id}"
