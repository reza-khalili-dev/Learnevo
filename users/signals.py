from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


@receiver(post_migrate)
def create_user_groups(sender, **kwargs):
    group_names = ["Admin Level 1", "Admin Level 2", "Instructor", "Student"]
    for name in group_names:
        Group.objects.get_or_create(name=name)


@receiver(post_save, sender=User)
def sync_role_to_group(sender, instance, created, **kwargs):
    role_map = {
        'manager': 'Admin Level 1',
        'employee': 'Admin Level 2',
        'instructor': 'Instructor',
        'student': 'Student',
    }

    target_group_name = role_map.get(instance.role)
    if not target_group_name:
        return

    lms_groups = Group.objects.filter(name__in=role_map.values())

    for g in lms_groups:
        if instance.groups.filter(pk=g.pk).exists():
            instance.groups.remove(g)

    target_group, _ = Group.objects.get_or_create(name=target_group_name)
    instance.groups.add(target_group)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
