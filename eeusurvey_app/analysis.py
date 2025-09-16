# analysis.py (or inside a view)

from collections import defaultdict
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404

from eeusurvey_app.models import Answer, Survey, SurveyResponse

def analyze_survey_responses(survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    responses = SurveyResponse.objects.filter(survey=survey).prefetch_related(
        'answers__question__category',
        'answers__selected_options'
    )

    analysis = {
        "total_responses": responses.count(),
        "by_category": {},
        "key_choices": {k.key: k.description for k in survey.keys.all()}, # type: ignore
        "completion_rate": {},  # per question
    }
    # Group questions by category
    questions = survey.questions.prefetch_related('options') # type: ignore
    for question in questions:
        cat_name = question.category.name
        if cat_name not in analysis["by_category"]:
            analysis["by_category"][cat_name] = {
                "questions": [],
                "avg_rating": None,
                "distribution": []
            }

        q_data = {
            "id": question.id,
            "text": question.question_text,
            "type": question.question_type,
            "answers": []
        }

        answers = Answer.objects.filter(question=question)

        if question.question_type == "rating":
            stats = answers.aggregate(avg=Avg('rating_value'), count=Count('id'))
            ratings = answers.values('rating_value').annotate(count=Count('rating_value'))

            rating_dist = {i: 0 for i in range(1, 6)}
            for r in ratings:
                rating_dist[r['rating_value']] = r['count']

            q_data.update({
                "avg_rating": round(stats['avg'] or 0, 2),
                "total_answers": stats['count'],
                "rating_distribution": rating_dist
            })

        elif question.question_type in ['single_choice', 'multi_select']:
            option_counts = defaultdict(int)
            total = 0
            for answer in answers:
                if question.question_type == 'single_choice':
                    opts = answer.selected_options.all()
                    for opt in opts:
                        option_counts[opt.text] += 1
                        total += 1
                else:  # multi_select
                    opts = answer.selected_options.all()
                    for opt in opts:
                        option_counts[opt.text] += 1
                    total += 1 if opts.exists() else 0

            q_data["selection_counts"] = dict(option_counts)
            q_data["total_responded"] = total

        elif question.question_type == "number":
            stats = answers.exclude(number_value=None).aggregate(
                avg=Avg('number_value'),
                count=Count('id')
            )
            q_data["avg_value"] = round(stats['avg'] or 0, 2)
            q_data["total_answers"] = stats['count']

        analysis["by_category"][cat_name]["questions"].append(q_data)

    # Compute category averages for rating questions
    for cat_name, cat_data in analysis["by_category"].items():
        rating_totals = []
        for q in cat_data["questions"]:
            if q.get("avg_rating") is not None:
                rating_totals.append(q["avg_rating"])
        if rating_totals:
            cat_data["avg_rating"] = round(sum(rating_totals) / len(rating_totals), 2)

    return analysis