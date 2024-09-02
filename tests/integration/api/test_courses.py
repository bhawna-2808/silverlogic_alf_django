from datetime import timedelta

from django.core import mail
from django.utils import timezone

import mock
import pytest
from freezegun import freeze_time
from rest_framework.test import APIClient

from apps.facilities.models import FacilityUser, TrainingsTimedAuthToken
from apps.trainings.models import (
    EmployeeCourse,
    TaskHistory,
    TaskHistoryCertificate,
    TaskHistoryCertificatePage,
)

import tests.factories as f
import tests.helpers as h
from tests.fixtures import pdf_file
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class TestCourseViewset(ApiMixin):
    view_list = "courses-list"
    view_detail = "courses-detail"
    view_name = view_list

    def test_guest_cant_create(self, client):
        r = client.post(self.reverse())
        h.responseUnauthorized(r)

    def test_guest_cant_list(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_guest_cant_view(self, client):
        self.view_name = self.view_detail
        course = f.CourseFactory()
        r = client.get(self.reverse(kwargs={"pk": course.pk}))
        h.responseUnauthorized(r)

    def test_guest_cant_edit(self, client):
        self.view_name = self.view_detail
        course = f.CourseFactory()
        r = client.patch(self.reverse(kwargs={"pk": course.pk}), {"name": "test"})
        h.responseUnauthorized(r)

    def test_user_can_create_course(self, manager_client):
        task_type = f.TaskTypeFactory()
        data = {
            "name": "course 1",
            "description": "description 1",
            "objective": "objective 1",
            "duration": "1 day",
            "minimum_score": 4,
            "language": 1,
            "task_type": task_type.pk,
        }
        r = manager_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert r.data["name"] == data["name"]

    def test_employee_user_cant_create(self, employee_client):
        task_type = f.TaskTypeFactory()
        data = {
            "name": "course 1",
            "description": "description 1",
            "objective": "objective 1",
            "minimum_score": 4,
            "language": 1,
            "task_type": task_type.pk,
        }
        r = employee_client.post(self.reverse(), data)
        h.responseForbidden(r)

    def test_user_can_retreive_course(self, employee_client):
        self.view_name = self.view_detail
        course = f.CourseFactory(published=True)
        r = employee_client.get(self.reverse(kwargs={"pk": course.pk}))
        h.responseOk(r)
        assert r.data["name"] == course.name

    def test_user_can_list_course(self, manager_client):
        f.CourseFactory.create_batch(size=3, published=True)
        f.CourseFactory()
        r = manager_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 4

    def test_course_list_filter_by_language(self, employee_client):
        courseSpanish = f.CourseFactory(published=True, language=2)
        r = employee_client.get(self.reverse(query_params={"language": 2}))
        h.responseOk(r)
        assert len(r.data) == 1
        assert r.data[0]["id"] == courseSpanish.id

    def test_course_list_filter_by_name(self, employee_client):
        course = f.CourseFactory(published=True, name="Course 1")
        f.CourseFactory(published=True, name="Course 2")
        r = employee_client.get(self.reverse(query_params={"name": "Course 1"}))
        h.responseOk(r)
        assert len(r.data) == 1
        assert r.data[0]["id"] == course.id

    def test_course_list_contains_course_taken(self, employee_client):
        course = f.CourseFactory(published=True)
        f.EmployeeCourseFactory(employee=employee_client.user.employee, course=course)
        f.EmployeeCourseFactory(course=course)
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data[0]["course_taken"]) == 1

    def test_employee_user_can_list_published_course(self, employee_client):
        f.CourseFactory.create_batch(size=3, published=True)
        f.CourseFactory()
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 3

    def test_user_can_delete_course(self, manager_client):
        self.view_name = self.view_detail
        course = f.CourseFactory()
        r = manager_client.delete(self.reverse(kwargs={"pk": course.pk}))
        h.responseNoContent(r)

    def test_employee_user_cant_delete_course(self, employee_client):
        self.view_name = self.view_detail
        course = f.CourseFactory()
        r = employee_client.delete(self.reverse(kwargs={"pk": course.pk}))
        h.responseForbidden(r)

    def test_last_course_item_started(self, employee_client):
        course = f.CourseFactory(published=True)
        course_item1 = f.CourseItemFactory(course=course)
        course_item2 = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(
            course_item=course_item1, employee=employee_client.user.employee
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item2,
            employee=employee_client.user.employee,
            started_at=timezone.now() + timezone.timedelta(seconds=1),
        )
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        assert r.data[0]["last_started_course_item"] != course_item1.id
        assert r.data[0]["last_started_course_item"] == course_item2.id

    def test_course_item_answer_correct(self, employee_client):
        course = f.CourseFactory(published=True)
        course_item1 = f.CourseItemFactory(course=course)
        course_item2 = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(
            course_item=course_item1, employee=employee_client.user.employee
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item2,
            employee=employee_client.user.employee,
            started_at=timezone.now() + timezone.timedelta(seconds=1),
        )

    def test_reset_last_started_course_item(self, employee_client):
        self.view_name = self.view_detail
        course = f.CourseFactory(published=True)
        course_item = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(course_item=course_item, employee=employee_client.user.employee)
        r = employee_client.get(self.reverse(kwargs={"pk": course.pk}))
        h.responseOk(r)
        assert r.data["last_started_course_item"] == course_item.id
        self.view_name = "courses-reset"
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}))
        h.responseOk(r)
        assert r.data["last_started_course_item"] is None

    def test_object_in_list_keys(self, employee_client):
        self.view_name = self.view_list
        f.CourseFactory.create_batch(size=3, published=True)
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        expected = {
            "id",
            "task_type",
            "name",
            "description",
            "objective",
            "duration",
            "published",
            "items",
            "course_taken",
            "minimum_score",
            "max_points",
            "last_started_course_item",
            "language",
            "statement_required",
        }
        actual = set(r.data[0].keys())
        assert expected == actual

    def test_object_in_expanded_list_keys(self, employee_client):
        self.view_name = self.view_list
        f.CourseItemLetterSizeImageFactory(item__course__published=True)
        r = employee_client.get(self.reverse(query_params={"expand": "items"}))
        h.responseOk(r)
        expected = {
            "id",
            "task_type",
            "name",
            "description",
            "objective",
            "duration",
            "published",
            "items",
            "course_taken",
            "minimum_score",
            "max_points",
            "last_started_course_item",
            "language",
            "statement_required",
        }
        actual = set(r.data[0].keys())
        assert expected == actual
        actual_items = set(r.data[0]["items"][0].keys())
        actual_items_expected = {
            "id",
            "course",
            "title",
            "order",
            "image",
            "texts",
            "videos",
            "letter_size_image",
            "boolean",
            "choices",
            "started_at",
            "min_duration",
        }
        assert actual_items_expected == actual_items

    def test_count_course_items(self, employee_client):
        course = f.CourseFactory(published=True)
        course_item = f.CourseItemFactory(course=course)
        f.CourseItemTextFactory(item=course_item)
        f.CourseItemTextFactory(item=course_item)
        f.CourseItemBooleanFactory(item=course_item)
        f.CourseItemBooleanFactory(item=course_item)
        f.CourseItemMultiChoiceFactory(item=course_item)
        f.CourseItemVideoFactory(item=course_item)
        f.CourseItemLetterSizeImageFactory(item=course_item)
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        assert r.data[0]["max_points"] == 3


class TestCourseItemViewset(ApiMixin):
    view_list = "course-items-list"
    view_detail = "course-items-detail"
    view_name = view_list

    def test_guest_cant_create(self, client):
        r = client.post(self.reverse())
        h.responseUnauthorized(r)

    def test_guest_cant_list(self, client):
        r = client.get(self.reverse())
        h.responseUnauthorized(r)

    def test_guest_cant_view(self, client):
        self.view_name = self.view_detail
        item = f.CourseItemFactory()
        r = client.get(self.reverse(kwargs={"pk": item.pk}))
        h.responseUnauthorized(r)

    def test_guest_cant_edit(self, client):
        self.view_name = self.view_detail
        item = f.CourseItemFactory()
        r = client.patch(self.reverse(kwargs={"pk": item.pk}), {"title": "test"})
        h.responseUnauthorized(r)

    def test_user_can_create_course_item(self, manager_client):
        course = f.CourseFactory()
        data = {
            "title": "title 1",
            "course": course.pk,
        }
        r = manager_client.post(self.reverse(), data)
        h.responseCreated(r)
        assert r.data["title"] == data["title"]

    def test_employee_user_cant_create(self, employee_client):
        course = f.CourseFactory()
        data = {
            "title": "title 1",
            "course": course.pk,
        }
        r = employee_client.post(self.reverse(), data)
        h.responseForbidden(r)

    def test_user_can_retreive_course_item(self, employee_client):
        self.view_name = self.view_detail
        course = f.CourseFactory(published=True)
        item = f.CourseItemFactory(course=course)
        r = employee_client.get(self.reverse(kwargs={"pk": item.pk}))
        h.responseOk(r)
        assert r.data["title"] == item.title

    def test_user_can_list_course_item(self, manager_client):
        f.CourseItemFactory.create_batch(size=3)
        r = manager_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 3

    def test_employee_user_can_list_published_course_item(self, employee_client):
        course = f.CourseFactory(published=True)
        f.CourseItemFactory.create_batch(size=3, course=course)
        f.CourseItemFactory()
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 3

    def test_user_can_delete_course_item(self, manager_client):
        self.view_name = self.view_detail
        item = f.CourseItemFactory()
        r = manager_client.delete(self.reverse(kwargs={"pk": item.pk}))
        h.responseNoContent(r)

    def test_employee_user_cant_delete_course(self, employee_client):
        self.view_name = self.view_detail
        item = f.CourseItemFactory()
        r = employee_client.delete(self.reverse(kwargs={"pk": item.pk}))
        h.responseForbidden(r)

    def test_object_in_list_keys(self, employee_client):
        self.view_name = self.view_list
        f.CourseItemFactory.create_batch(size=3, course__published=True)
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        expected = {
            "id",
            "course",
            "title",
            "order",
            "image",
            "texts",
            "videos",
            "letter_size_image",
            "boolean",
            "choices",
            "started_at",
            "min_duration",
        }
        actual = set(r.data[0].keys())
        assert expected == actual


class TestCourseItems(ApiMixin):
    view_name = "courses-items"

    def test_user_can_list_course_items(self, employee_client):
        course = f.CourseFactory(published=True)
        f.CourseItemFactory.create_batch(size=2, course=course)
        r = employee_client.get(self.reverse(kwargs={"pk": course.pk}))
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_add_course_item(self, manager_client, image_base64):
        course = f.CourseFactory(published=True)
        data = {
            "title": "item 2",
            "order": 1,
            "texts": [
                {"question": "question 1", "answer": "answer 1", "order": 0},
                {"question": "question 2", "answer": "answer 2", "order": 0},
                {"question": "question 3", "answer": "answer 3", "order": 0},
            ],
            "videos": [
                {"link": "example.com", "embedded_url": "example.com", "order": 0},
                {"link": "example.com", "embedded_url": "example.com", "order": 0},
                {"link": "example.com", "embedded_url": "example.com", "order": 0},
            ],
            "boolean": [
                {"question": "question 4", "answer": False, "order": 0},
                {"question": "question 5", "answer": True, "order": 0},
            ],
            "choices": [
                {
                    "question": "question 6",
                    "options": [
                        {"label": "option a"},
                        {"label": "option b"},
                        {"label": "option c"},
                    ],
                    "answers": [{"label": "option a"}],
                    "order": 0,
                },
                {
                    "question": "question 7",
                    "options": [
                        {"label": "option a"},
                        {"label": "option b"},
                        {"label": "option c"},
                    ],
                    "answers": [{"label": "option a"}],
                    "order": 0,
                },
            ],
            "letter_size_image": [
                {
                    "image": image_base64,
                },
            ],
        }
        r = manager_client.post(self.reverse(kwargs={"pk": course.pk}), data=data)
        h.responseCreated(r)
        assert r.data["course"] == course.pk

    def test_user_can_add_course_item_with_image(self, manager_client, image_base64):
        course = f.CourseFactory(published=True)
        data = {
            "title": "item 2",
            "order": 1,
            "image": image_base64,
            "texts": [{"question": "question 1", "answer": "answer 1", "order": 0}],
        }
        r = manager_client.post(self.reverse(kwargs={"pk": course.pk}), data=data)
        h.responseCreated(r)
        assert r.data["course"] == course.pk

    def test_employee_user_cant_add_course_item(self, employee_client):
        course = f.CourseFactory(published=True)
        data = {"title": "title 1", "order": 2}
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}), data=data)
        h.responseForbidden(r)


class TestCourseOpen(ApiMixin):
    view_name = "courses-open"
    view_detail = "courses-detail"

    def test_user_can_open_course(self, employee_client):
        task_type = f.TaskTypeFactory(name="Task type name")
        course = f.CourseFactory(published=True, minimum_score=1, task_type=task_type)
        f.CourseItemFactory(course=course)
        task = f.TaskFactory(type=task_type, employee=employee_client.user.employee)
        r = employee_client.get(self.reverse(kwargs={"pk": course.pk}))
        h.responseOk(r)

        assert r.data["task"]["id"] == task.id

    def test_open_course_should_create_task_if_employee_not_assigned(self, employee_client):
        task_type = f.TaskTypeFactory(name="Task type name")
        course = f.CourseFactory(published=True, minimum_score=1, task_type=task_type)
        f.CourseItemFactory(course=course)
        task = f.TaskFactory(type=task_type)
        r = employee_client.get(self.reverse(kwargs={"pk": course.pk}))
        h.responseOk(r)

        assert r.data["task"]["id"] != task.id  # different task id created


class TestCourseComplete(ApiMixin):
    view_name = "courses-complete"
    view_detail = "courses-detail"

    def test_user_can_submit_complete_course(self, employee_client):
        course = f.CourseFactory(published=True, minimum_score=1)
        course_item = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(
            course_item=course_item,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}))
        h.responseCreated(r)
        assert r.data["employee"] == employee_client.user.employee.id
        assert r.data["status"] == EmployeeCourse.STATUSES.completed
        assert r.data["is_approved"] is True

    def test_user_fails_minimum_score_not_reached(self, employee_client):
        course = f.CourseFactory(published=True, minimum_score=2)
        course_item = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(
            course_item=course_item,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item,
            employee=employee_client.user.employee,
            is_correct=False,
        )
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}))
        h.responseCreated(r)
        assert r.data["is_approved"] is False

    def test_user_complete_started_course(self, employee_client):
        course = f.CourseFactory(published=True)
        ec = f.EmployeeCourseFactory(course=course, employee=employee_client.user.employee)
        course_item_1 = f.CourseItemFactory(course=course)
        course_item_2 = f.CourseItemFactory(course=course)
        course_item_3 = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(
            course_item=course_item_1,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_2,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_3,
            employee=employee_client.user.employee,
            is_correct=False,
        )
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}))
        h.responseCreated(r)
        ec.refresh_from_db()
        assert ec.score == 2
        assert r.data["completed_date"] == timezone.now().date().strftime("%Y-%m-%d")
        assert r.data["id"] == ec.id
        assert r.data["status"] == EmployeeCourse.STATUSES.completed

    def test_user_complete_started_course_with_date(self, employee_client):
        course = f.CourseFactory(published=True)
        ec = f.EmployeeCourseFactory(course=course, employee=employee_client.user.employee)
        course_item_1 = f.CourseItemFactory(course=course)
        course_item_2 = f.CourseItemFactory(course=course)
        course_item_3 = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(
            course_item=course_item_1,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_2,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_3,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        data = {
            "completed_date": "2019-06-10",
        }
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}), data)
        h.responseCreated(r)
        ec.refresh_from_db()
        assert ec.score == 3
        assert r.data["completed_date"] == "2019-06-10"
        assert r.data["id"] == ec.id
        assert r.data["status"] == EmployeeCourse.STATUSES.completed

    @mock.patch(
        "apps.api.views.generate_pdf_template_object",
        mock.MagicMock(return_value=pdf_file),
    )
    @mock.patch("apps.trainings.utils.attach_pdf_to_email", mock.MagicMock(return_value=None))
    def test_complete_course_create_taskhistory_and_certificate(self, employee_client):
        course = f.CourseFactory(published=True, minimum_score=2)
        course_item_1 = f.CourseItemFactory(course=course)
        course_item_2 = f.CourseItemFactory(course=course)
        course_item_3 = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(
            course_item=course_item_1,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_2,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_3,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.TaskFactory(employee=employee_client.user.employee, type=course.task_type)
        admin_position = f.PositionFactory(name="Administrator")
        facility = employee_client.user.employee.facility
        f.EmployeeFactory(
            facility=facility,
            receives_emails=True,
            positions=[admin_position],
            email="admin@test.com",
        )
        f.EmployeeFactory(receives_emails=True, positions=[admin_position], email="admin@test.com")
        f.CourseItemFactory.create_batch(size=5, course=course)
        history = TaskHistory.objects.all()
        data = {"start_date": "2019-03-31", "completed_date": "2019-04-01"}
        assert len(history) == 0
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}), data)
        h.responseCreated(r)
        assert r.data["status"] == 1
        history = TaskHistory.objects.all()
        assert len(history) == 1
        assert TaskHistoryCertificate.objects.all().count() == 1
        assert TaskHistoryCertificatePage.objects.all().count() == 2
        assert len(mail.outbox) == 1

    @mock.patch(
        "apps.api.views.generate_pdf_template_object",
        mock.MagicMock(return_value=pdf_file),
    )
    @mock.patch("apps.trainings.utils.attach_pdf_to_email", mock.MagicMock(return_value=None))
    def test_complete_course_create_taskhistory_and_certificate_mobile(self, employee_client):
        course = f.CourseFactory(published=True, minimum_score=2)
        f.TaskFactory(employee=employee_client.user.employee, type=course.task_type)
        admin_position = f.PositionFactory(name="Administrator")
        facility = employee_client.user.employee.facility
        f.EmployeeFactory(
            facility=facility,
            receives_emails=True,
            positions=[admin_position],
            email="admin@test.com",
        )
        f.EmployeeFactory(receives_emails=True, positions=[admin_position], email="admin@test.com")
        f.CourseItemFactory.create_batch(size=5, course=course)
        history = TaskHistory.objects.all()
        data = {"score": 4, "start_date": "2019-03-31", "completed_date": "2019-04-01"}
        assert len(history) == 0
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}), data)
        h.responseCreated(r)
        assert r.data["status"] == 1
        history = TaskHistory.objects.all()
        assert len(history) == 1
        assert TaskHistoryCertificate.objects.all().count() == 1
        assert TaskHistoryCertificatePage.objects.all().count() == 2
        assert len(mail.outbox) == 1

    @mock.patch(
        "apps.api.views.generate_pdf_template_object",
        mock.MagicMock(return_value=pdf_file),
    )
    @mock.patch("apps.trainings.utils.attach_pdf_to_email", mock.MagicMock(return_value=None))
    def test_complete_course_create_taskhistory_and_certificate_with_signature(
        self, employee_client, image_base64
    ):
        course = f.CourseFactory(published=True, minimum_score=2, statement_required=True)
        course_item_1 = f.CourseItemFactory(course=course)
        course_item_2 = f.CourseItemFactory(course=course)
        course_item_3 = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(
            course_item=course_item_1,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_2,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_3,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.TaskFactory(employee=employee_client.user.employee, type=course.task_type)
        admin_position = f.PositionFactory(name="Administrator")
        facility = employee_client.user.employee.facility
        f.EmployeeFactory(
            facility=facility,
            receives_emails=True,
            positions=[admin_position],
            email="admin@test.com",
        )
        f.EmployeeFactory(receives_emails=True, positions=[admin_position], email="admin@test.com")
        f.CourseItemFactory.create_batch(size=5, course=course)
        history = TaskHistory.objects.all()
        data = {
            "score": 4,
            "start_date": "2019-03-31",
            "completed_date": "2019-04-01",
            "signature": image_base64,
        }
        assert len(history) == 0
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}), data)
        h.responseCreated(r)
        assert r.data["status"] == 1
        history = TaskHistory.objects.all()
        assert len(history) == 1
        assert TaskHistoryCertificate.objects.all().count() == 1
        assert TaskHistoryCertificatePage.objects.all().count() == 3
        assert len(mail.outbox) == 1

    def test_complete_course_asks_for_signature_if_required(self, employee_client, image_base64):
        course = f.CourseFactory(published=True, minimum_score=2, statement_required=True)
        f.TaskFactory(employee=employee_client.user.employee, type=course.task_type)

        f.EmployeeCourseFactory(course=course, employee=employee_client.user.employee)
        course_item_1 = f.CourseItemFactory(course=course)
        course_item_2 = f.CourseItemFactory(course=course)
        course_item_3 = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(
            course_item=course_item_1,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_2,
            employee=employee_client.user.employee,
            is_correct=True,
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_3,
            employee=employee_client.user.employee,
            is_correct=True,
        )

        data = {"score": 4, "start_date": "2019-03-31", "completed_date": "2019-04-01"}
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}), data)
        h.responseBadRequest(r)

        assert r.data["non_field_errors"][0] == "Signature required for this course"

    def test_failed_complete_course_not_create_taskhistory(self, employee_client):
        course = f.CourseFactory(published=True, minimum_score=4)
        f.TaskFactory(employee=employee_client.user.employee, type=course.task_type)
        f.CourseItemFactory.create_batch(size=5, course=course)
        history = TaskHistory.objects.all()
        data = {"score": 2, "start_date": "2019-03-31", "completed_date": "2019-04-01"}
        assert len(history) == 0
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}), data)
        h.responseCreated(r)
        assert r.data["status"] == 1
        history = TaskHistory.objects.all()
        assert len(history) == 0
        assert len(mail.outbox) == 0

    def test_complete_resets_last_started_course_item(self, employee_client):
        complete_view = self.view_name
        self.view_name = self.view_detail
        course = f.CourseFactory(published=True)
        course_item = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(course_item=course_item, employee=employee_client.user.employee)
        #  here we GET the last_started
        r = employee_client.get(self.reverse(kwargs={"pk": course.pk}))
        h.responseOk(r)
        assert r.data["last_started_course_item"] == course_item.id
        #  here we post the complete
        self.view_name = complete_view
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}))
        h.responseCreated(r)
        #  here we GET the last_started again
        self.view_name = self.view_detail
        r = employee_client.get(self.reverse(kwargs={"pk": course.pk}))
        h.responseOk(r)
        assert r.data["last_started_course_item"] is None


class TestCourseStart(ApiMixin):
    view_name = "courses-start"

    def test_user_start_course(self, employee_client):
        course = f.CourseFactory(published=True)
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}))
        h.responseCreated(r)
        assert r.data["employee"] == employee_client.user.employee.id
        assert r.data["start_date"] == timezone.now().date().strftime("%Y-%m-%d")
        assert r.data["status"] == EmployeeCourse.STATUSES.in_progress

    def test_user_start_course_with_date(self, employee_client):
        course = f.CourseFactory(published=True)
        data = {
            "start_date": "2019-03-31",
        }
        r = employee_client.post(self.reverse(kwargs={"pk": course.pk}), data)
        h.responseCreated(r)
        assert r.data["employee"] == employee_client.user.employee.id
        assert r.data["start_date"] == "2019-03-31"
        assert r.data["status"] == EmployeeCourse.STATUSES.in_progress


def get_item(published=True):
    course = f.CourseFactory(published=published)
    return f.CourseItemFactory(course=course)


class TestCourseItemTexts(ApiMixin):
    view_name = "course-items-texts"

    def test_user_can_list_course_item_texts(self, employee_client):
        item = get_item()
        f.CourseItemTextFactory.create_batch(size=2, item=item)
        r = employee_client.get(self.reverse(kwargs={"pk": item.pk}))
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_add_course_item_texts(self, manager_client):
        item = get_item()
        data = {"question": "question 1", "answer": "answer 1", "order": 2}
        r = manager_client.post(self.reverse(kwargs={"pk": item.pk}), data=data)
        h.responseCreated(r)
        assert r.data["item"] == item.pk

    def test_employee_user_cant_add_course_item_texts(self, employee_client):
        item = get_item()
        data = {"question": "question 1", "answer": "answer 1", "order": 2}
        r = employee_client.post(self.reverse(kwargs={"pk": item.pk}), data=data)
        h.responseForbidden(r)


class TestCourseItemVideo(ApiMixin):
    view_name = "course-items-videos"

    def test_user_can_list_course_item_videos(self, employee_client):
        item = get_item()
        f.CourseItemVideoFactory.create_batch(size=2, item=item)
        r = employee_client.get(self.reverse(kwargs={"pk": item.pk}))
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_add_course_item_videos(self, manager_client):
        item = get_item()
        data = {"link": "link", "embedded_url": "embedded_url", "order": 2}
        r = manager_client.post(self.reverse(kwargs={"pk": item.pk}), data=data)
        h.responseCreated(r)
        assert r.data["item"] == item.pk

    def test_employee_user_cant_add_course_item_videos(self, employee_client):
        item = get_item()
        data = {"link": "link 1", "embedded_url": "embedded_url 1", "order": 2}
        r = employee_client.post(self.reverse(kwargs={"pk": item.pk}), data=data)
        h.responseForbidden(r)


class TestCourseItemLetterSizeImage(ApiMixin):
    view_name = "course-items-letter-size-image"

    def test_user_can_list_course_item_letter_size_image(self, employee_client):
        item = get_item()
        f.CourseItemLetterSizeImageFactory.create_batch(size=2, item=item)
        r = employee_client.get(self.reverse(kwargs={"pk": item.pk}))
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_add_course_item_letter_size_image(self, manager_client, image_base64):
        item = get_item()
        data = {"image": image_base64}
        r = manager_client.post(self.reverse(kwargs={"pk": item.pk}), data=data)
        h.responseCreated(r)
        assert r.data["item"] == item.pk

    def test_employee_user_cant_add_course_item_letter_size_image(
        self, employee_client, image_base64
    ):
        item = get_item()
        data = {"image": image_base64}
        r = employee_client.post(self.reverse(kwargs={"pk": item.pk}), data=data)
        h.responseForbidden(r)


class TestCourseItemBoolean(ApiMixin):
    view_name = "course-items-boolean"

    def test_user_can_list_course_item_boolean(self, employee_client):
        item = get_item()
        f.CourseItemBooleanFactory.create_batch(size=2, item=item)
        r = employee_client.get(self.reverse(kwargs={"pk": item.pk}))
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_add_course_item_boolean(self, manager_client):
        item = get_item()
        data = {"question": "question 5", "answer": True, "order": 2}
        r = manager_client.post(self.reverse(kwargs={"pk": item.pk}), data=data)
        h.responseCreated(r)
        assert r.data["item"] == item.pk

    def test_employee_user_cant_add_course_item_boolean(self, employee_client):
        item = get_item()
        data = {"question": "question 5", "answer": True, "order": 2}
        r = employee_client.post(self.reverse(kwargs={"pk": item.pk}), data=data)
        h.responseForbidden(r)


class TestCourseItemMultiChoice(ApiMixin):
    view_name = "course-items-choices"

    def test_user_can_list_course_item_multi_choice(self, employee_client):
        item = get_item()
        f.CourseItemMultiChoiceFactory.create_batch(size=2, item=item)
        r = employee_client.get(self.reverse(kwargs={"pk": item.pk}))
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_add_course_item_multi_choice(self, manager_client):
        item = get_item()
        data = {
            "question": "question 8",
            "options": [{"label": "label 1"}, {"label": "label 2"}],
            "answers": [
                {"label": "label 2"},
            ],
            "order": 2,
        }
        r = manager_client.post(self.reverse(kwargs={"pk": item.pk}), data=data)
        h.responseCreated(r)
        assert r.data["item"] == item.pk
        assert len(r.data["options"]) == 2

    def test_employee_user_cant_add_course_item_multi_choice(self, employee_client):
        item = get_item()
        data = {
            "question": "question 8",
            "options": [{"label": "label 1"}, {"label": "label 2"}],
            "answers": [
                {"label": "label 2"},
            ],
            "order": 2,
        }
        r = employee_client.post(self.reverse(kwargs={"pk": item.pk}), data=data)
        h.responseForbidden(r)


class TestCourseItemTextViewset(ApiMixin):
    view_name = "course-item-texts-list"
    view_detail = "course-item-texts-detail"

    def test_user_can_list_item_texts(self, employee_client):
        item = get_item()
        f.CourseItemTextFactory.create_batch(size=2, item=item)
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_update_item_texts(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        texts = f.CourseItemTextFactory.create_batch(size=2, item=item)
        data = {
            "question": "question edited",
        }
        r = manager_client.patch(self.reverse(kwargs={"pk": texts[0].pk}), data=data)
        h.responseOk(r)
        assert r.data["question"] == data["question"]

    def test_user_can_retreive_item_texts(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        texts = f.CourseItemTextFactory.create_batch(size=2, item=item)
        r = manager_client.get(self.reverse(kwargs={"pk": texts[0].pk}))
        h.responseOk(r)
        assert r.data["id"] == texts[0].pk

    def test_manager_user_can_delete_item_texts(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        item_texts = f.CourseItemTextFactory.create_batch(size=2, item=item)
        r = manager_client.delete(self.reverse(kwargs={"pk": item_texts[0].pk}))
        h.responseNoContent(r)


class TestCourseItemVideoViewset(ApiMixin):
    view_name = "course-item-videos-list"
    view_detail = "course-item-videos-detail"

    def test_user_can_list_item_videos(self, employee_client):
        item = get_item()
        f.CourseItemVideoFactory.create_batch(size=2, item=item)
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_update_item_videos(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        item_videos = f.CourseItemVideoFactory.create_batch(size=2, item=item)
        data = {
            "link": "link edited",
        }
        r = manager_client.patch(self.reverse(kwargs={"pk": item_videos[0].pk}), data=data)
        h.responseOk(r)
        assert r.data["link"] == data["link"]

    def test_user_can_retreive_item_videos(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        item_videos = f.CourseItemVideoFactory.create_batch(size=2, item=item)
        r = manager_client.get(self.reverse(kwargs={"pk": item_videos[0].pk}))
        h.responseOk(r)
        assert r.data["id"] == item_videos[0].pk

    def test_manager_user_can_delete_item_videos(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        item_videos = f.CourseItemVideoFactory.create_batch(size=2, item=item)
        r = manager_client.delete(self.reverse(kwargs={"pk": item_videos[0].pk}))
        h.responseNoContent(r)


class TestCourseItemBooleanViewset(ApiMixin):
    view_name = "course-item-boolean-list"
    view_detail = "course-item-boolean-detail"

    def test_user_can_list_item_boolean(self, employee_client):
        item = get_item()
        f.CourseItemBooleanFactory.create_batch(size=2, item=item)
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_update_item_boolean(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        item_boolean = f.CourseItemBooleanFactory.create_batch(size=2, item=item)
        data = {
            "question": "question edited",
        }
        r = manager_client.patch(self.reverse(kwargs={"pk": item_boolean[0].pk}), data=data)
        h.responseOk(r)
        assert r.data["question"] == data["question"]

    def test_user_can_retreive_item_boolean(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        item_boolean = f.CourseItemBooleanFactory.create_batch(size=2, item=item)
        r = manager_client.get(self.reverse(kwargs={"pk": item_boolean[0].pk}))
        h.responseOk(r)
        assert r.data["id"] == item_boolean[0].pk

    def test_manager_user_can_delete_item_boolean(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        item_boolean = f.CourseItemBooleanFactory.create_batch(size=2, item=item)
        r = manager_client.delete(self.reverse(kwargs={"pk": item_boolean[0].pk}))
        h.responseNoContent(r)


class TestCourseItemMultiChoiceViewset(ApiMixin):
    view_name = "course-item-choices-list"
    view_detail = "course-item-choices-detail"

    def test_user_can_list_item_multi_choice(self, employee_client):
        item = get_item()
        f.CourseItemMultiChoiceFactory.create_batch(size=2, item=item)
        r = employee_client.get(self.reverse())
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_update_item_multi_choice(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        item_multi_choice = f.CourseItemMultiChoiceFactory.create_batch(size=2, item=item)
        data = {
            "question": "question edited",
        }
        r = manager_client.patch(self.reverse(kwargs={"pk": item_multi_choice[0].pk}), data=data)
        h.responseOk(r)
        assert r.data["question"] == data["question"]

    def test_user_can_retreive_item_multi_choice(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        item_multi_choice = f.CourseItemMultiChoiceFactory.create_batch(size=2, item=item)
        r = manager_client.get(self.reverse(kwargs={"pk": item_multi_choice[0].pk}))
        h.responseOk(r)
        assert r.data["id"] == item_multi_choice[0].pk

    def test_manager_user_can_delete_item_multi_choice(self, manager_client):
        self.view_name = self.view_detail
        item = get_item()
        item_multi_choice = f.CourseItemMultiChoiceFactory.create_batch(size=2, item=item)
        r = manager_client.delete(self.reverse(kwargs={"pk": item_multi_choice[0].pk}))
        h.responseNoContent(r)


class TestMultiChoiceOptionViewset(ApiMixin):
    view_name = "course-item-choices-options"

    def test_user_can_list_item_multi_choice_option(self, employee_client):
        item = get_item()
        item_multi_choice = f.CourseItemMultiChoiceFactory.create_batch(size=2, item=item)
        options = f.MultiChoiceOptionFactory.create_batch(size=2)
        item_multi_choice[0].options.set(options)
        r = employee_client.get(self.reverse(kwargs={"pk": item_multi_choice[0].pk}))
        h.responseOk(r)
        assert len(r.data) == 2

    def test_user_can_add_item_multi_choice_option(self, manager_client):
        item = get_item()
        item_multi_choice = f.CourseItemMultiChoiceFactory.create_batch(size=2, item=item)
        r = manager_client.post(
            self.reverse(kwargs={"pk": item_multi_choice[0].pk}), {"label": "option 1"}
        )
        h.responseCreated(r)
        assert r.data["label"] == "option 1"


class TestMultiChoiceAnswerViewset(ApiMixin):
    view_name = "course-item-choices-answers"

    def test_user_can_list_item_multi_choice_answers(self, employee_client):
        item = get_item()
        item_multi_choice = f.CourseItemMultiChoiceFactory.create_batch(size=2, item=item)
        options = f.MultiChoiceOptionFactory.create_batch(size=2)
        item_multi_choice[0].options.set(options)
        item_multi_choice[0].answers.set([options[0]])
        r = employee_client.get(self.reverse(kwargs={"pk": item_multi_choice[0].pk}))
        h.responseOk(r)
        assert len(r.data) == 1

    def test_user_can_add_item_multi_choice_answer(self, manager_client):
        item = get_item()
        item_multi_choice = f.CourseItemMultiChoiceFactory.create_batch(size=2, item=item)
        options = f.MultiChoiceOptionFactory.create_batch(size=2)
        item_multi_choice[0].options.set(options)
        r = manager_client.post(
            self.reverse(kwargs={"pk": item_multi_choice[0].pk}),
            {"label": options[0].label},
        )
        h.responseCreated(r)
        assert r.data["id"] == options[0].pk


class TestCourseItemStart(ApiMixin):
    view_name = "course-items-start"

    def test_user_start_course_item(self, employee_client):
        course = f.CourseFactory(published=True)
        course_item = f.CourseItemFactory(course=course)
        r = employee_client.post(self.reverse(kwargs={"pk": course_item.pk}))
        h.responseCreated(r)
        assert r.data["employee"] == employee_client.user.employee.id
        assert r.data["started_at"] is not None

    def test_user_start_course_item_with_date_time(self, employee_client):
        course = f.CourseFactory(published=True)
        course_item = f.CourseItemFactory(course=course)
        data = {
            "started_at": "2019-06-11T10:00:00-04:00",
        }
        r = employee_client.post(self.reverse(kwargs={"pk": course_item.pk}), data)
        h.responseCreated(r)
        assert r.data["employee"] == employee_client.user.employee.id
        assert r.data["started_at"] == "2019-06-11T10:00:00-04:00"


class TestCourseItemComplete(ApiMixin):
    view_name = "course-items-item-complete"

    def test_user_can_complete_item(self, employee_client):
        course = f.CourseFactory(published=True, minimum_score=2)
        fu_2 = f.FacilityUserFactory(role=FacilityUser.Role.trainings_user)
        f.EmployeeFactory(user=fu_2.user)
        course_item_1 = f.CourseItemFactory(course=course)
        course_item_2 = f.CourseItemFactory(course=course)
        course_item_3 = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(
            course_item=course_item_1, employee=fu_2.user.employee, is_correct=True
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_2, employee=fu_2.user.employee, is_correct=True
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_3, employee=fu_2.user.employee, is_correct=True
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_1, employee=employee_client.user.employee
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_2, employee=employee_client.user.employee
        )
        f.EmployeeCourseItemFactory(
            course_item=course_item_3, employee=employee_client.user.employee
        )
        f.CourseItemBooleanFactory(item=course_item_1, answer=True)
        f.CourseItemBooleanFactory(item=course_item_2, answer=False)
        mc_1 = f.CourseItemMultiChoiceFactory(item=course_item_3)
        mco_1 = f.MultiChoiceOptionFactory()
        mc_1.options.add(mco_1)
        mc_1.answers.add(mco_1)
        data = {"answer": True}

        r = employee_client.post(self.reverse(kwargs={"pk": course_item_1.pk}), data)
        h.responseOk(r)
        assert r.data["is_correct"] is True
        assert r.data["total"] == 3
        assert r.data["score"] == 1

        r = employee_client.post(self.reverse(kwargs={"pk": course_item_2.pk}), data)
        h.responseOk(r)
        assert r.data["is_correct"] is False
        assert r.data["total"] == 3
        assert r.data["score"] == 1

        data = {"answer": mco_1.pk + 1}

        r = employee_client.post(self.reverse(kwargs={"pk": course_item_3.pk}), data)
        h.responseOk(r)
        assert r.data["is_correct"] is False
        assert r.data["total"] == 3
        assert r.data["score"] == 1

        data = {"answer": mco_1.pk}

        r = employee_client.post(self.reverse(kwargs={"pk": course_item_3.pk}), data)
        h.responseOk(r)
        assert r.data["is_correct"] is True
        assert r.data["total"] == 3
        assert r.data["score"] == 2

    @freeze_time("2020-01-06")
    def test_complete_item_should_set_completed_at_date(self, employee_client):
        course = f.CourseFactory(published=True, minimum_score=2)
        course_item_1 = f.CourseItemFactory(course=course)
        employee_course_item = f.EmployeeCourseItemFactory(
            course_item=course_item_1, employee=employee_client.user.employee
        )

        r = employee_client.post(self.reverse(kwargs={"pk": course_item_1.pk}), {"answer": True})
        h.responseOk(r)
        employee_course_item.refresh_from_db()
        assert employee_course_item.completed_at is not None

    @pytest.mark.parametrize(
        "role",
        [
            FacilityUser.Role.account_admin,
            FacilityUser.Role.trainings_user,
            FacilityUser.Role.manager,
        ],
    )
    def test_complete_item_token_should_never_expire_allowed_users(self, role):
        employee_client = APIClient()
        facility_user = f.FacilityUserFactory(role=FacilityUser.Role.trainings_user)
        f.EmployeeFactory(user=facility_user.user)

        course = f.CourseFactory(published=True, minimum_score=2)
        course_item_1 = f.CourseItemFactory(course=course)
        employee_course_item = f.EmployeeCourseItemFactory(
            course_item=course_item_1, employee=facility_user.user.employee
        )
        token = TrainingsTimedAuthToken.objects.create(user=facility_user.user)
        token.expires = timezone.now() - timedelta(days=1)
        token.save()
        employee_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key} ")

        r = employee_client.post(self.reverse(kwargs={"pk": course_item_1.pk}), {"answer": True})
        h.responseOk(r)

        employee_course_item.refresh_from_db()
        assert employee_course_item.completed_at is not None

    @pytest.mark.parametrize("role", [FacilityUser.Role.examiner])
    def test_complete_item_token_should_expire_non_allowed_users(self, role):
        employee_client = APIClient()
        facility_user = f.FacilityUserFactory(role=role)
        f.EmployeeFactory(user=facility_user.user)

        course = f.CourseFactory(published=True, minimum_score=2)
        course_item_1 = f.CourseItemFactory(course=course)
        f.EmployeeCourseItemFactory(course_item=course_item_1, employee=facility_user.user.employee)
        token = TrainingsTimedAuthToken.objects.create(user=facility_user.user)
        token.expires = timezone.now() - timedelta(days=1)
        token.save()
        employee_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key} ")

        r = employee_client.post(self.reverse(kwargs={"pk": course_item_1.pk}), {"answer": True})
        h.responseUnauthorized(r)

    def test_user_cant_complete_item_without_starting_it_first(self, employee_client):
        course = f.CourseFactory(published=True, minimum_score=2)
        course_item_1 = f.CourseItemFactory(course=course)
        f.CourseItemBooleanFactory(item=course_item_1, answer=True)
        data = {"answer": True}
        r = employee_client.post(self.reverse(kwargs={"pk": course_item_1.pk}), data)
        h.responseBadRequest(r)
