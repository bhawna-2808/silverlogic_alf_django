import logging
from datetime import date

from django.db.models import Q

from apps.api.trainings.views import generate_course_certificate
from apps.trainings.models import Course, Employee, EmployeeCourse, TaskHistory

logger = logging.getLogger(__name__)


def generate_task_history(employee_id, task_type_id):
    dt = date.today()
    employee = Employee.objects.get(id=employee_id)
    TaskHistory.objects.create(
        completion_date=dt,
        expiration_date=dt,
        status=2,
        employee=employee,
        type_id=task_type_id,
    )


def regenerate_course_certificate(employee, course_id):
    task_history = (
        employee.trainings_taskhistory_set.filter(type__course__pk=course_id)
        .order_by("-id", "-created")
        .first()
    )
    course = Course.objects.filter(id=course_id).first()
    if not course:
        logger.info(f"Course not found for {employee.full_name}")
        return "course_not_found"
    if task_history:
        if employee.courses.filter(course=course).count() > 1:
            logger.info(f"Multiple employee course found for {employee.full_name}")
        employee_course = employee.courses.filter(course=course).order_by("-created").first()
        if hasattr(task_history, "certificate"):
            logger.info(f"Deleting existing course certificate for {employee.full_name}")
            task_history.certificate.delete()
        generate_course_certificate(employee, employee.facility, task_history, employee_course)
        logger.info(f"Course Certificate Regenerated for {employee.full_name}")
        return "certificate_regenerated"
    else:
        logger.info(f"Task History not found for {employee.full_name}")
        return "task_history_not_found"


def apply_signature_to_courses(courses_qs, employees_qs=None):
    qs = EmployeeCourse.objects.filter(
        course__in=courses_qs,
    )
    if employees_qs:
        qs = qs.filter(employee__in=employees_qs)
    for employee_course in qs:
        course = employee_course.course
        employee = employee_course.employee
        if not bool(employee_course.signature):
            ec_signature = EmployeeCourse.objects.filter(
                Q(signature__isnull=False) & ~Q(signature=""),
                employee=employee,
            ).first()
            if ec_signature:
                employee_course.signature = ec_signature.signature
                employee_course.save()

        result = regenerate_course_certificate(employee, course.id)
        if result == "task_history_not_found":
            generate_task_history(employee.id, course.task_type_id)
            regenerate_course_certificate(employee, course.id)
