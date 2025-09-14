from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group
from django.dispatch import receiver



@receiver(post_migrate)

def create_user_groups(sender , **kwargs):
    groups = ["Admin Level 1", "Admin Level 2", "Instructor", "Student"]
    for group in groups:
        Group.objects.get_or_create(name=group)