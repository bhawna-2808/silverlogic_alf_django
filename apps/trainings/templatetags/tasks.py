from django import template
from django.utils import timezone

from ..models import TaskStatus

register = template.Library()


def task_status_name(task):
    if task.status == TaskStatus.open:
        if task.type.is_training:
            return "Awaiting Certificate"
        return "Awaiting Documentation"
    elif task.status == TaskStatus.scheduled:
        if task.scheduled_event:
            if (task.scheduled_event.start_time - timezone.now()).days < 0:
                if task.type.is_training:
                    return "Awaiting Certificate"
                return "Awaiting Documentation"
    return task.get_status_display()


register.filter("task_status_name", task_status_name)
