# Create a new file: eeusurvey_app/templatetags/survey_extras.py

from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide the value by the argument."""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calculate percentage."""
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def to_json(value):
    """Convert value to JSON."""
    return mark_safe(json.dumps(value))

@register.simple_tag
def progress_bar(value, max_value, width=200):
    """Generate a simple progress bar."""
    try:
        percentage = (float(value) / float(max_value)) * 100 if max_value > 0 else 0
        return mark_safe(
            f'<div style="background: #e9ecef; width: {width}px; height: 20px; border-radius: 10px; overflow: hidden;">'
            f'<div style="background: #007cba; height: 100%; width: {percentage}%; transition: width 0.3s;"></div>'
            f'</div>'
        )
    except (ValueError, TypeError):
        return ''

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary."""
    return dictionary.get(key)

@register.simple_tag
def survey_status_badge(survey):
    """Generate a status badge for surveys."""
    if survey.is_active:
        color = "green"
        text = "Active"
        icon = "✅"
    else:
        color = "red"
        text = "Inactive"
        icon = "❌"
    
    return mark_safe(
        f'<span style="color: {color}; font-weight: bold;">{icon} {text}</span>'
    )

@register.simple_tag
def response_rate_badge(current, total):
    """Generate a response rate badge."""
    try:
        rate = (float(current) / float(total)) * 100 if total > 0 else 0
        
        if rate >= 80:
            color = "#28a745"  # Green
            icon = "🟢"
        elif rate >= 60:
            color = "#ffc107"  # Yellow
            icon = "🟡"
        else:
            color = "#dc3545"  # Red
            icon = "🔴"
        
        return mark_safe(
            f'<span style="color: {color}; font-weight: bold;">'
            f'{icon} {rate:.1f}% ({current}/{total})'
            f'</span>'
        )
    except (ValueError, TypeError):
        return mark_safe('<span>N/A</span>')

@register.filter
def format_large_number(value):
    """Format large numbers with K, M suffixes."""
    try:
        num = float(value)
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return str(int(num))
    except (ValueError, TypeError):
        return str(value)