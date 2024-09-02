from datetime import date

from django.db.models import Q
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import (
    Antirequisite,
    Employee,
    Facility,
    FacilityDefault,
    FacilityQuestion,
    FacilityQuestionRule,
    GlobalRequirement,
    Position,
    Responsibility,
    Task,
    TaskHistory,
    TaskHistoryStatus,
    TaskStatus,
    TaskType,
    TrainingEvent,
)
from .tasks import (
    apply_global_requirement,
    apply_type_responsibility,
    reapply_employee_positions,
    reapply_employee_responsibilities,
    reapply_position,
)


@receiver(post_save, sender=Facility)
def create_default_instance_for_facility(sender, instance, **kwargs):
    if not hasattr(instance, "default"):
        FacilityDefault.objects.create(facility=instance)
    if instance.point is None:
        instance.geolocation


@receiver(m2m_changed, sender=Facility.questions.through)
def facility_questions_changed(sender, instance, action, pk_set, **kwargs):
    facility = instance

    if action == "post_add":
        for question in FacilityQuestion.objects.filter(pk__in=pk_set):
            for rule in question.rules.all():
                for employee in Employee.objects.filter(facility=facility, positions=rule.position):
                    employee.other_responsibilities.add(rule.responsibility)

    elif action == "post_remove":
        for question in FacilityQuestion.objects.filter(pk__in=pk_set):
            for rule in question.rules.all():
                for employee in Employee.objects.filter(facility=facility, positions=rule.position):
                    employee.other_responsibilities.remove(rule.responsibility)


@receiver(pre_save, sender=Task)
def task_no_duplicates_created(sender, instance, **kwargs):
    # We only care about creations.
    if instance.pk:
        return

    try:
        task = Task.objects.get(employee=instance.employee, type=instance.type)

        if instance.due_date and instance.due_date < task.due_date:
            task.due_date = instance.due_date

        instance.__dict__ = task.__dict__

    except Task.DoesNotExist:
        pass


@receiver(post_save, sender=FacilityQuestionRule)
def update_employee_responsibilities(sender, instance, created, **kwargs):
    """
    Updates employee responsibilities whenever a rule is create or modified
    """
    facilities = instance.facility_question.facility_set.all()
    for facility in facilities:
        employees = facility.employee_set.filter(positions=instance.position)
        for employee in employees:
            employee.other_responsibilities.add(instance.responsibility)


def create_task_for_responsibility(employee, responsibility):
    types = TaskType.objects.filter(required_for__pk=responsibility.pk).filter(
        Q(facility=employee.facility) | Q(facility=None)
    )
    if not types.exists():
        return

    for type in types:
        is_antirequisite = Antirequisite.objects.filter(task_type=type).exists()
        if is_antirequisite:
            # Handled by the antirequisite signals.
            continue
        else:
            task, _ = Task.objects.update_or_create(
                employee=employee,
                type=type,
                is_optional=True,
                defaults={"is_optional": False},
            )
            task.refresh_from_db()
            task.recompute_due_date()


@receiver(m2m_changed, sender=Employee.positions.through)
def employee_positions_changed(sender, instance, pk_set, action, **kwargs):
    employee = instance
    if action == "post_add":
        # Fetches responsibility ID's associated with each position as
        # determined by the rules set by facility questions
        responsibility_ids_of_rules = (
            FacilityQuestionRule.objects.filter(facility_question__facility=employee.facility)
            .filter(position_id__in=pk_set)
            .distinct()
            .values_list("responsibility", flat=True)
        )

        # Fetches responsibilities required by positions and rules
        responsibilities = Responsibility.objects.distinct().filter(
            Q(position__pk__in=pk_set) | Q(id__in=responsibility_ids_of_rules)
        )

        # Updates the responsibilities, doesn't add duplicates
        employee.other_responsibilities.add(*[r for r in responsibilities])
    elif action == "post_remove":
        remaining_positions = employee.positions.all()
        # Fetches responsibility ID's associated with each position as
        # determined by the rules set by facility questions
        responsibility_ids_of_rules = (
            FacilityQuestionRule.objects.filter(facility_question__facility=employee.facility)
            .filter(position_id__in=pk_set)
            .exclude(position__in=remaining_positions)
            .distinct()
            .values_list("responsibility", flat=True)
        )

        # Fetches responsibilities required by positions and rules
        responsibilities = (
            Responsibility.objects.distinct()
            .filter(
                Q(position__pk__in=pk_set)
                | Q(id__in=responsibility_ids_of_rules)
                | Q(question_position_restriction_id__in=pk_set)
            )
            .exclude(Q(position__in=remaining_positions))
        )

        # Updates the responsibilities, doesn't add duplicates
        employee.other_responsibilities.remove(*[r for r in responsibilities])


@receiver(m2m_changed, sender=Employee.other_responsibilities.through)
def employee_other_responsibilities_changed(sender, instance, pk_set, action, **kwargs):
    employee = instance
    if action == "post_add":
        for responsibility in Responsibility.objects.filter(pk__in=pk_set):
            create_task_for_responsibility(employee, responsibility)

        antirequisites = get_employee_antirequisites(employee)
        for antirequisite in antirequisites:
            add_antirequisite_task(employee, antirequisite)
    elif action == "post_remove":
        antirequisites = get_employee_antirequisites(employee)
        non_required_task_types = (
            TaskType.objects.filter(required_for__pk__in=pk_set)
            .exclude(required_for__in=employee.other_responsibilities.all())
            .exclude(pk__in=antirequisites.values_list("task_type_id", flat=True))
            .exclude(globalrequirement__isnull=False)
            .distinct()
        )
        (Task.objects.filter(employee=employee, type__in=non_required_task_types).delete())


@receiver(m2m_changed, sender=TaskType.required_for.through)
def task_type_responsibility_added(sender, instance, pk_set, action, **kwargs):
    task_type = instance
    if action == "post_add":
        # running on background to prevent timeout
        apply_type_responsibility.delay(list(pk_set), task_type.id)


@receiver(m2m_changed, sender=TrainingEvent.attendees.through)
def training_event_attendees_changed(sender, instance, pk_set, action, **kwargs):
    if action == "post_add":
        tasks = Task.objects.filter(
            Q(status=TaskStatus.open) | Q(status=TaskStatus.scheduled),
            type=instance.training_for,
            employee__id__in=pk_set,
        )
        tasks.update(status=TaskStatus.scheduled)
        instance.employee_tasks.add(*tasks)

    if action == "post_remove":
        tasks = Task.objects.filter(
            Q(status=TaskStatus.open) | Q(status=TaskStatus.scheduled),
            type=instance.training_for,
            employee__id__in=pk_set,
        )
        tasks.update(status=TaskStatus.open)
        instance.employee_tasks.remove(*tasks)

    if action == "post_clear":
        instance.employee_tasks.update(status=TaskStatus.open)
        instance.employee_tasks.clear()


def get_antirequisite_employees(antirequisite):
    """ """
    completed_employee_ids = (
        TaskHistory.objects.filter(
            status=TaskHistoryStatus.completed, type=antirequisite.antirequisite_of
        )
        .values_list("employee_id", flat=True)
        .distinct()
    )

    return (
        Employee.objects.filter(date_of_hire__gte=antirequisite.valid_after_hire_date)
        .filter(trainings_task_set__type=antirequisite.antirequisite_of)
        .exclude(pk__in=completed_employee_ids)
    )


def get_employee_antirequisites(employee):
    completed_task_type_ids = (
        employee.trainings_taskhistory_set.filter(status=TaskHistoryStatus.completed)
        .values_list("type_id", flat=True)
        .distinct()
    )

    return Antirequisite.objects.filter(valid_after_hire_date__lte=employee.date_of_hire).exclude(
        antirequisite_of_id__in=completed_task_type_ids
    )


@receiver(post_save, sender=Antirequisite)
def create_or_update_antirequisite_task(sender, instance, **kwargs):
    employees = get_antirequisite_employees(instance)
    for employee in employees:
        add_antirequisite_task(employee, instance)


def add_antirequisite_task(employee, antirequisite):
    one_off = TaskHistory.objects.filter(
        employee=employee,
        type=antirequisite.task_type,
        type__is_one_off=True,
        status=TaskHistoryStatus.completed,
        completion_date__gte=antirequisite.valid_after_hire_date,
    ).first()

    if one_off:
        return

    due_date = antirequisite.due_date or employee.date_of_hire

    responsibility_added_task = Task.objects.filter(
        employee=employee, type=antirequisite.task_type, antirequisite=None
    ).first()

    if responsibility_added_task:
        responsibility_added_task.due_date = due_date
        responsibility_added_task.save()

    task, created = Task.objects.get_or_create(
        antirequisite=antirequisite,
        employee=employee,
        defaults={
            "type": antirequisite.task_type,
            "employee": employee,
            "antirequisite": antirequisite,
            "due_date": due_date,
        },
    )

    if not created:
        task.due_date = due_date
        task.type = antirequisite.task_type
        task.save()


@receiver(post_save, sender=TaskType)
def check_task_type_capacity(sender, instance, **kwargs):
    task_type = instance

    if (
        task_type.initial_min_capacity == task_type.min_capacity
        and task_type.initial_max_capacity == task_type.max_capacity
    ):
        return

    for task in Task.objects.filter(type=task_type):
        task.recompute_due_date()


@receiver(post_save, sender=Facility)
def check_facility_capacity(sender, instance, **kwargs):
    facility = instance

    if facility.initial_capacity == facility.capacity:
        return

    task_types = TaskType.objects.filter(Q(facility=facility) | Q(facility__isnull=True))
    for task_type in task_types:
        for employee in Employee.objects.filter(facility=facility):
            task = Task.objects.create(employee=employee, type=task_type)
            task.recompute_due_date()


@receiver(pre_save, sender=Employee)
def on_save_employee(sender, instance: Employee, **kwargs):
    user_activated = instance.tracker.has_changed("is_active") and instance.is_active
    user_deactivated = (
        instance.tracker.has_changed("deactivation_date") and instance.deactivation_date
    )
    if user_deactivated and instance.deactivation_date <= date.today():
        instance.is_active = False
    if user_activated:
        instance.is_reactivated = True
    if user_deactivated:
        instance.is_reactivated = False


@receiver(post_save, sender=Employee)
def on_post_save_employee(sender, instance, created, **kwargs):
    employee = instance

    if created:
        for global_requirement in GlobalRequirement.objects.all():
            task = Task.objects.create(employee=employee, type=global_requirement.task_type)
            task.recompute_due_date()
    else:
        if instance.tracker.has_changed("date_of_hire"):
            reapply_employee_positions.delay(instance.id)
            reapply_employee_responsibilities.delay(instance.id)


@receiver(post_save, sender=GlobalRequirement)
def create_global_requirement(sender, instance, created, **kwargs):
    global_requirement = instance

    if created:
        apply_global_requirement.delay(global_requirement.pk)


@receiver(post_delete, sender=GlobalRequirement)
def delete_global_requirement(sender, instance, **kwargs):
    Task.objects.filter(type=instance.task_type).delete()


@receiver(m2m_changed, sender=Position.responsibilities.through)
def position_responsibilities_changed(sender, instance, pk_set, action, reverse, **kwargs):
    if not reverse:
        position = instance
        reapply_position.delay(position.pk)
    else:
        responsibility = instance
        for position in Position.objects.filter(responsibilities=responsibility):
            reapply_position.delay(position.pk)
