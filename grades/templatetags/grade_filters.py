from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """ضرب دو عدد"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """تقسیم دو عدد"""
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (ValueError, TypeError):
        return 0

@register.filter
def grade_type_count(grades, grade_type):
    """شمارش نمرات بر اساس نوع"""
    return len([g for g in grades if g.grade_type == grade_type])