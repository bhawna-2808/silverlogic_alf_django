from apps.api.trainings.serializers import (
    EmployeeSimpleSerializer,
    ResponsibilityEducationRequirementReadSerializer,
    TaskReadSerializer,
)
from apps.facilities.models import FacilityUser
from apps.utils.general import Enumeration

from .models import Task, TaskHistoryStatus


def compute_compliance_for_facility(facility, current_date, user):
    employee_compliance_list = []
    result = {"employee_compliance_list": employee_compliance_list}
    facility_satisfied = True
    employees = facility.employee_set.all()

    if user.facility_users.role == FacilityUser.Role.trainings_user or (
        user.facility_users.role == FacilityUser.Role.manager
        and not user.facility_users.can_see_staff
    ):
        employees = [user.employee]

    for employee in employees:
        employee_compliance = compute_compliance_for_employee(employee, current_date)
        employee_compliance["employee"] = EmployeeSimpleSerializer(employee).data
        facility_satisfied = facility_satisfied and employee_compliance.get(
            "employee_satisfied", False
        )
        employee_compliance_list.append(employee_compliance)
    result["facility_satisfied"] = facility_satisfied
    return result


def get_responsibilities_for_employee(employee):
    id_to_model_map = {}

    for position in employee.positions.all():
        for responsibility in position.responsibilities.all():
            id_to_model_map[responsibility.id] = responsibility

    for responsibility in employee.other_responsibilities.all():
        id_to_model_map[responsibility.id] = responsibility

    return list(id_to_model_map.values())


def compute_compliance_for_employee(employee, current_date):
    requirement_map = {}
    for responsibility in get_responsibilities_for_employee(employee):
        for requirement in responsibility.education_requirements.all():
            requirement_map[requirement.id] = requirement

    compliance_list = []
    result = {"compliance_list": compliance_list}
    employee_satisfied = True
    for requirement in list(requirement_map.values()):
        compliance = compute_compliance_for_requirement(requirement, employee, current_date)
        serializer = ResponsibilityEducationRequirementReadSerializer(requirement)
        compliance["requirement"] = serializer.data
        employee_satisfied = employee_satisfied and compliance.get("requirement_satisfied", False)
        compliance_list.append(compliance)
    result["employee_satisfied"] = employee_satisfied

    return result


compliance_code_enum = Enumeration(
    (1, "on_track", "On Track"),
    (2, "falling_behind", "Falling Behind"),
    (3, "far_behind", "Far Behind"),
)


def compute_compliance_code(start_date, current_date, end_date, accumulated_hours, required_hours):
    accumulated_times_all_days = accumulated_hours * (end_date - start_date).days
    required_times_used_days = required_hours * (current_date - start_date).days
    if accumulated_times_all_days >= required_times_used_days:
        return compliance_code_enum.on_track
    if accumulated_times_all_days >= 0.8 * required_times_used_days:
        return compliance_code_enum.falling_behind
    return compliance_code_enum.far_behind


def compute_compliance_for_requirement(requirement, employee, current_date):
    result = {}

    # compute base task
    base_task_qs = (
        employee.trainings_taskhistory_set.filter(status=TaskHistoryStatus.completed)
        .filter(type_id=requirement.interval_base.id)
        .order_by("-completion_date")
    )
    if not base_task_qs.count():
        result["base_task_not_completed"] = True
        return result
    base_task = base_task_qs.first()
    first_task = base_task_qs.last()
    # compute time interval information
    # cdmbtcd current_date minus interval_task.completion_date
    cdmbtcd = current_date - base_task.completion_date
    interval_count = int(cdmbtcd.total_seconds() / requirement.timeperiod.total_seconds())
    cycles_count = (
        int(
            (current_date - first_task.completion_date).total_seconds()
            / requirement.timeperiod.total_seconds()
        )
        + 1
    )
    start_date = base_task.completion_date + (interval_count * requirement.timeperiod)
    end_date = start_date + requirement.timeperiod

    start_over = result["start_over"] = requirement.start_over
    if start_over:
        start_date = base_task.completion_date
        end_date = start_date + requirement.timeperiod
        cycles_count = 1

    result["base_task_completion_date"] = base_task.completion_date
    result["interval_count"] = interval_count
    result["cycles_count"] = cycles_count
    result["start_date"] = start_date
    result["end_date"] = end_date

    # compute accumulated hours
    task_history = employee.trainings_taskhistory_set.filter(status=TaskHistoryStatus.completed)

    # Accumulated hours for the current cycle
    accumulated_hours = 0
    # Accumulated hours for all cycles
    accumulated_total = 0
    for task in task_history:
        for credit in task.type.education_credits.filter(type=requirement.type):
            if task.completion_date >= start_date and task.completion_date < end_date:
                accumulated_hours += task.credit_hours
            if not start_over:
                accumulated_total += task.credit_hours
        if start_over:
            accumulated_total = accumulated_hours

    if start_over:
        if current_date > end_date and accumulated_hours < requirement.hours:
            result["base_task_not_completed"] = True
            return result

    result["accumulated_hours"] = accumulated_hours
    result["accumulated_total"] = accumulated_total

    result["compliance_code"] = compute_compliance_code(
        start_date, current_date, end_date, requirement.hours, accumulated_hours
    )
    result["requirement_satisfied"] = accumulated_hours >= requirement.hours

    tasks = Task.objects.filter(
        employee=employee,
        type__required_for=requirement.responsibility,
        type__education_credits__type=requirement.type,
    ).exclude(type=requirement.interval_base)

    result["tasks"] = [TaskReadSerializer(t).data for t in tasks]

    return result
