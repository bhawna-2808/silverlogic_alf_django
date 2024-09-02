from datetime import date, timedelta

from django.test import TestCase

from apps.facilities.models import FacilityUser
from apps.trainings.continuing_education import (
    compliance_code_enum,
    compute_compliance_code,
    compute_compliance_for_employee,
    compute_compliance_for_facility,
    compute_compliance_for_requirement,
    get_responsibilities_for_employee,
)
from apps.trainings.models import TaskHistoryStatus, continuing_education_type_enum

import tests.factories as f
from tests.factories import (
    EmployeeFactory,
    FacilityFactory,
    PositionFactory,
    ResponsibilityEducationRequirementFactory,
    ResponsibilityFactory,
    TaskHistoryFactory,
    TaskTypeEducationCreditFactory,
    TaskTypeFactory,
)


class RequirementTests(TestCase):
    def test_incomplete_education_type(self):
        base_tasktype = TaskTypeFactory()
        requirement = ResponsibilityEducationRequirementFactory(
            hours=77, timeperiod=timedelta(days=700), interval_base=base_tasktype
        )
        tasktype1 = TaskTypeFactory()
        tasktype2 = TaskTypeFactory()
        TaskTypeEducationCreditFactory(tasktype=base_tasktype)
        TaskTypeEducationCreditFactory(tasktype=tasktype1)
        TaskTypeEducationCreditFactory(
            tasktype=tasktype2, type=continuing_education_type_enum.admin
        )
        employee = EmployeeFactory()
        base_completion_date = date(2014, 7, 7)
        base_expiration_date = date(2016, 7, 7)
        completion_date = date(2015, 1, 1)
        expiration_date = date(2017, 1, 1)
        sim_date = date(2016, 1, 1)
        TaskHistoryFactory(
            employee=employee,
            type=base_tasktype,
            credit_hours=1,
            completion_date=base_completion_date,
            expiration_date=base_expiration_date,
        )
        TaskHistoryFactory(
            employee=employee,
            type=tasktype1,
            credit_hours=2,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        TaskHistoryFactory(
            employee=employee,
            type=tasktype1,
            completion_date=completion_date,
            expiration_date=expiration_date,
            status=TaskHistoryStatus.incomplete,
        )
        TaskHistoryFactory(
            employee=employee,
            type=tasktype2,
            credit_hours=4,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        summary = compute_compliance_for_requirement(requirement, employee, sim_date)
        target_hours_sum = 3
        self.assertEqual(summary.get("accumulated_hours", 0), target_hours_sum)

    def test_acc_hours_satisfied_base_credit_old_base_task(self):
        base_tasktype = TaskTypeFactory()
        requirement = ResponsibilityEducationRequirementFactory(
            hours=21, timeperiod=timedelta(days=700), interval_base=base_tasktype
        )
        tasktype1 = TaskTypeFactory()
        tasktype2 = TaskTypeFactory()
        base_credit = TaskTypeEducationCreditFactory(tasktype=base_tasktype)  # noqa
        credit1 = TaskTypeEducationCreditFactory(tasktype=tasktype1)  # noqa
        credit2 = TaskTypeEducationCreditFactory(tasktype=tasktype2)  # noqa
        employee = EmployeeFactory()
        old_base_completion_date = date(2002, 7, 7)
        old_base_expiration_date = date(2004, 7, 7)
        base_completion_date = date(2014, 7, 7)
        base_expiration_date = date(2016, 7, 7)
        completion_date = date(2015, 1, 1)
        expiration_date = date(2017, 1, 1)
        sim_date = date(2016, 1, 1)
        old_base_task = TaskHistoryFactory(  # noqa
            employee=employee,
            type=base_tasktype,
            credit_hours=5,
            completion_date=old_base_completion_date,
            expiration_date=old_base_expiration_date,
        )
        base_task = TaskHistoryFactory(  # noqa
            employee=employee,
            type=base_tasktype,
            credit_hours=5,
            completion_date=base_completion_date,
            expiration_date=base_expiration_date,
        )
        task1 = TaskHistoryFactory(  # noqa
            employee=employee,
            type=tasktype1,
            credit_hours=3,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        task2 = TaskHistoryFactory(  # noqa
            employee=employee,
            type=tasktype1,
            credit_hours=3,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        task3 = TaskHistoryFactory(  # noqa
            employee=employee,
            type=tasktype2,
            credit_hours=11,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        summary = compute_compliance_for_requirement(requirement, employee, sim_date)
        target_hours_sum = 5 + 3 + 3 + 11
        self.assertEqual(summary.get("accumulated_hours", 0), target_hours_sum)
        self.assertTrue(summary.get("requirement_satisfied", False))

    def test_interval_count_not_satisfied_old_credit(self):
        base_tasktype = TaskTypeFactory()
        requirement = ResponsibilityEducationRequirementFactory(
            hours=13, timeperiod=timedelta(days=90), interval_base=base_tasktype
        )
        tasktype1 = TaskTypeFactory()
        base_credit = TaskTypeEducationCreditFactory(tasktype=base_tasktype)  # noqa
        credit1 = TaskTypeEducationCreditFactory(tasktype=tasktype1)  # noqa
        employee = EmployeeFactory()
        base_completion_date = date(2014, 7, 7)
        base_expiration_date = date(2016, 7, 7)
        completion_date = base_completion_date + timedelta(days=260)
        expiration_date = completion_date + timedelta(days=700)
        sim_date = base_completion_date + timedelta(days=300)
        base_task = TaskHistoryFactory(  # noqa
            employee=employee,
            type=base_tasktype,
            credit_hours=14,
            completion_date=base_completion_date,
            expiration_date=base_expiration_date,
        )
        task1 = TaskHistoryFactory(  # noqa
            employee=employee,
            type=tasktype1,
            credit_hours=15,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        summary = compute_compliance_for_requirement(requirement, employee, sim_date)
        self.assertEqual(summary.get("accumulated_hours", 0), 0)
        self.assertFalse(summary.get("requirement_satisfied", False))

    def test_base_task_not_completed(self):
        base_tasktype = TaskTypeFactory()
        requirement = ResponsibilityEducationRequirementFactory(
            hours=13, timeperiod=timedelta(days=90), interval_base=base_tasktype
        )
        employee = EmployeeFactory()
        sim_date = date(2015, 1, 1)
        summary = compute_compliance_for_requirement(requirement, employee, sim_date)
        self.assertTrue(summary.get("base_task_not_completed", False))
        self.assertFalse(summary.get("requirement_satisfied", False))

    def test_compliance_code(self):
        start = date(2014, 4, 1)
        end = date(2014, 5, 1)
        self.assertEqual(
            compliance_code_enum.on_track,
            compute_compliance_code(start, date(2014, 4, 1), end, 0, 100),
        )
        self.assertEqual(
            compliance_code_enum.on_track,
            compute_compliance_code(start, date(2014, 4, 4), end, 10, 100),
        )
        self.assertEqual(
            compliance_code_enum.falling_behind,
            compute_compliance_code(start, date(2014, 4, 4), end, 8, 100),
        )
        self.assertEqual(
            compliance_code_enum.far_behind,
            compute_compliance_code(start, date(2014, 4, 4), end, 7, 100),
        )
        self.assertEqual(
            compliance_code_enum.on_track,
            compute_compliance_code(start, date(2014, 5, 1), end, 100, 100),
        )


class EmployeeTests(TestCase):
    def test_get_responsibilities(self):
        resp1 = ResponsibilityFactory()
        resp2 = ResponsibilityFactory()
        resp3 = ResponsibilityFactory()
        resp4 = ResponsibilityFactory()
        resp5 = ResponsibilityFactory()
        pos1 = PositionFactory()
        pos2 = PositionFactory()
        pos1.responsibilities.set([resp1, resp2])
        pos1.save()
        pos2.responsibilities.set([resp2, resp3, resp4])
        pos2.save()
        employee = EmployeeFactory()
        employee.positions.set([pos1, pos2])
        employee.other_responsibilities.set([resp4, resp5])
        employee.save()
        resp_list = get_responsibilities_for_employee(employee)
        self.assertEqual(len(resp_list), 5)
        for respx in [resp1, resp2, resp3, resp4, resp5]:
            self.assertIn(respx, resp_list)

    def test_satisfied(self):
        base_tasktype = TaskTypeFactory()
        responsibility = ResponsibilityFactory()
        requirement1 = ResponsibilityEducationRequirementFactory(  # noqa
            hours=13,
            timeperiod=timedelta(days=700),
            interval_base=base_tasktype,
            responsibility=responsibility,
        )
        requirement2 = ResponsibilityEducationRequirementFactory(  # noqa
            hours=21,
            timeperiod=timedelta(days=700),
            interval_base=base_tasktype,
            responsibility=responsibility,
            type=continuing_education_type_enum.admin,
        )
        tasktype1 = TaskTypeFactory()
        tasktype2 = TaskTypeFactory()
        credit1 = TaskTypeEducationCreditFactory(tasktype=tasktype1)  # noqa
        credit2 = TaskTypeEducationCreditFactory(  # noqa
            tasktype=tasktype2, type=continuing_education_type_enum.admin
        )
        employee = EmployeeFactory()
        employee.other_responsibilities.set([responsibility])
        employee.save()
        base_completion_date = date(2014, 7, 7)
        base_expiration_date = date(2016, 7, 7)
        completion_date = date(2015, 1, 1)
        expiration_date = date(2017, 1, 1)
        sim_date = date(2016, 1, 1)
        base_task = TaskHistoryFactory(  # noqa
            employee=employee,
            type=base_tasktype,
            completion_date=base_completion_date,
            expiration_date=base_expiration_date,
        )
        task1 = TaskHistoryFactory(  # noqa
            employee=employee,
            type=tasktype1,
            credit_hours=13,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        task2 = TaskHistoryFactory(  # noqa
            employee=employee,
            type=tasktype2,
            credit_hours=21,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        summary = compute_compliance_for_employee(employee, sim_date)
        self.assertTrue(summary.get("employee_satisfied", False))

    def test_not_satisfied(self):
        base_tasktype = TaskTypeFactory()
        responsibility = ResponsibilityFactory()
        requirement1 = ResponsibilityEducationRequirementFactory(  # noqa
            hours=99,
            timeperiod=timedelta(days=700),
            interval_base=base_tasktype,
            responsibility=responsibility,
        )
        requirement2 = ResponsibilityEducationRequirementFactory(  # noqa
            hours=21,
            timeperiod=timedelta(days=700),
            interval_base=base_tasktype,
            responsibility=responsibility,
            type=continuing_education_type_enum.admin,
        )
        tasktype1 = TaskTypeFactory()
        tasktype2 = TaskTypeFactory()
        credit1 = TaskTypeEducationCreditFactory(tasktype=tasktype1)  # noqa
        credit2 = TaskTypeEducationCreditFactory(  # noqa
            tasktype=tasktype2, type=continuing_education_type_enum.admin
        )
        employee = EmployeeFactory()
        employee.other_responsibilities.set([responsibility])
        employee.save()
        base_completion_date = date(2014, 7, 7)
        base_expiration_date = date(2016, 7, 7)
        completion_date = date(2015, 1, 1)
        expiration_date = date(2017, 1, 1)
        sim_date = date(2016, 1, 1)
        base_task = TaskHistoryFactory(  # noqa
            employee=employee,
            type=base_tasktype,
            completion_date=base_completion_date,
            expiration_date=base_expiration_date,
        )
        task1 = TaskHistoryFactory(  # noqa
            employee=employee,
            type=tasktype1,
            credit_hours=13,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        task2 = TaskHistoryFactory(  # noqa
            employee=employee,
            type=tasktype2,
            credit_hours=21,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        summary = compute_compliance_for_employee(employee, sim_date)
        self.assertFalse(summary.get("employee_satisfied", False))


class FacilityTests(TestCase):
    def test_satisfied(self):
        facility = FacilityFactory()

        admin_user = f.UserFactory()
        f.FacilityUserFactory(user=admin_user, role=FacilityUser.Role.account_admin)

        trainings_user = f.UserFactory()
        f.FacilityUserFactory(user=trainings_user, role=FacilityUser.Role.trainings_user)

        base_tasktype = TaskTypeFactory()
        responsibility = ResponsibilityFactory()
        ResponsibilityEducationRequirementFactory(
            hours=13,
            timeperiod=timedelta(days=700),
            interval_base=base_tasktype,
            responsibility=responsibility,
        )
        tasktype = TaskTypeFactory()
        TaskTypeEducationCreditFactory(tasktype=tasktype)
        employee1 = EmployeeFactory(facility=facility)
        employee1.other_responsibilities.set([responsibility])
        employee1.save()
        employee2 = EmployeeFactory(facility=facility, user=trainings_user)
        employee2.other_responsibilities.set([responsibility])
        employee2.save()
        base_completion_date = date(2014, 7, 7)
        base_expiration_date = date(2016, 7, 7)
        completion_date = date(2015, 1, 1)
        expiration_date = date(2017, 1, 1)
        sim_date = date(2016, 1, 1)
        base_task1 = TaskHistoryFactory(  # noqa
            employee=employee1,
            type=base_tasktype,
            completion_date=base_completion_date,
            expiration_date=base_expiration_date,
        )
        base_task2 = TaskHistoryFactory(  # noqa
            employee=employee2,
            type=base_tasktype,
            completion_date=base_completion_date,
            expiration_date=base_expiration_date,
        )
        task1 = TaskHistoryFactory(  # noqa
            employee=employee1,
            type=tasktype,
            credit_hours=13,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        task2 = TaskHistoryFactory(  # noqa
            employee=employee2,
            type=tasktype,
            credit_hours=13,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        admin_user_summary = compute_compliance_for_facility(facility, sim_date, admin_user)
        self.assertTrue(admin_user_summary.get("facility_satisfied", False))

        trainings_user_summary = compute_compliance_for_facility(facility, sim_date, trainings_user)
        self.assertTrue(trainings_user_summary.get("facility_satisfied", False))

    def test_not_satisfied(self):
        facility = FacilityFactory()
        admin_user = f.UserFactory()
        f.FacilityUserFactory(user=admin_user, role=FacilityUser.Role.account_admin)

        trainings_user = f.UserFactory()
        f.FacilityUserFactory(user=trainings_user, role=FacilityUser.Role.trainings_user)

        base_tasktype = TaskTypeFactory()
        responsibility = ResponsibilityFactory()
        ResponsibilityEducationRequirementFactory(
            hours=13,
            timeperiod=timedelta(days=700),
            interval_base=base_tasktype,
            responsibility=responsibility,
        )
        tasktype = TaskTypeFactory()
        TaskTypeEducationCreditFactory(tasktype=tasktype)
        employee1 = EmployeeFactory(facility=facility)
        employee1.other_responsibilities.set([responsibility])
        employee1.save()
        employee2 = EmployeeFactory(facility=facility, user=trainings_user)
        employee2.other_responsibilities.set([responsibility])
        employee2.save()
        base_completion_date = date(2014, 7, 7)
        base_expiration_date = date(2016, 7, 7)
        completion_date = date(2015, 1, 1)
        expiration_date = date(2017, 1, 1)
        sim_date = date(2016, 1, 1)
        TaskHistoryFactory(
            employee=employee1,
            type=base_tasktype,
            completion_date=base_completion_date,
            expiration_date=base_expiration_date,
        )
        TaskHistoryFactory(
            employee=employee1,
            type=tasktype,
            credit_hours=13,
            completion_date=completion_date,
            expiration_date=expiration_date,
        )
        admin_user_summary = compute_compliance_for_facility(facility, sim_date, admin_user)
        self.assertFalse(admin_user_summary.get("facility_satisfied", False))

        trainings_user_summary = compute_compliance_for_facility(facility, sim_date, trainings_user)
        self.assertFalse(trainings_user_summary.get("facility_satisfied", False))
