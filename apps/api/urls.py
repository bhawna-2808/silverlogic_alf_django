from django.conf.urls import include
from django.urls import re_path

from .examiners.views import ExaminationRequestsViewSet, ExaminersViewSet
from .facilities.views import (
    BusinessAgreementViewSet,
    CloudCareFacilityViewSet,
    FacilityQuestionViewSet,
    FacilityViewSet,
)
from .login.views import LoginViewSet
from .plans.views import PlansViewSet
from .register.views import RegisterViewSet
from .residents.views import (
    CloudCareResidentsViewSet,
    ResidentArchived1823sViewSet,
    ResidentBedHoldViewSet,
    Residents1823PdfView,
    ResidentsAdmissionPdfView,
    ResidentsBlank1823PdfView,
    ResidentsFacesheetPdfView,
    ResidentsListPdfView,
    ResidentsViewSet,
)
from .routers import DefaultRouter
from .subscriptions.views import SponsorsViewSet, SubscriptionsViewSet
from .trainings.views import (
    AllowedTaskTypesViewSet,
    CloudCareEmployeeViewSet,
    CloudCarePositionViewSet,
    ComplianceView,
    ContinuingEducationSummaryForEmployeeView,
    ContinuingEducationSummaryForFacilityView,
    CourseItemBooleanViewSet,
    CourseItemMultiChoiceViewSet,
    CourseItemTextViewSet,
    CourseItemVideoViewSet,
    CourseItemViewSet,
    CourseViewSet,
    CurrentUserView,
    CustomTaskTypeViewSet,
    EmployeesCertificatesPdfView,
    EmployeesDetailPdfView,
    EmployeesListPdfView,
    EmployeeViewSet,
    PositionGroupViewSet,
    PositionViewSet,
    ResponsibilityEducationRequirementViewSet,
    ResponsibilityViewSet,
    TaskHistoryViewSet,
    TaskTypeEducationCreditViewSet,
    TaskTypeViewSet,
    TaskViewSet,
    TrainingEventPdfView,
    TrainingEventViewSet,
    UpcomingTasksPdfView,
)
from .tutorial_videos.views import TutorialVideosViewSet
from .user_invites.views import UserInvitesViewSet
from .users.views import UsersViewSet

router = DefaultRouter()

# Auth
router.register(r"signup", RegisterViewSet, basename="register")
router.register(r"login", LoginViewSet, basename="login")

# Facilities
router.register(r"facilities", FacilityViewSet, basename="facilities")
router.register(r"facility_questions", FacilityQuestionViewSet)
router.register(r"cloudcare/facilities", CloudCareFacilityViewSet, basename="cloudcare-facilities")


# Business Agreements
router.register(r"business_agreements", BusinessAgreementViewSet, basename="business-agreements")

# Trainings
router.register(r"employees", EmployeeViewSet, basename="employee")
router.register(r"employees/(?P<parent_pk>\d+)/allowed_task_types", AllowedTaskTypesViewSet)
router.register(r"cloudcare/employees", CloudCareEmployeeViewSet, basename="cloudcare-employees")
router.register(r"responsibilities", ResponsibilityViewSet)
router.register(r"responsibility_education_requirements", ResponsibilityEducationRequirementViewSet)
router.register(r"positions", PositionViewSet)
router.register(r"cloudcare/positions", CloudCarePositionViewSet, basename="cloudcare-positions")

router.register(r"task_type_education_credits", TaskTypeEducationCreditViewSet)
router.register(r"task_types", TaskTypeViewSet)
router.register(r"custom_task_types", CustomTaskTypeViewSet, basename="custom-task-types")
router.register(r"tasks", TaskViewSet)
router.register(r"task_histories", TaskHistoryViewSet)
router.register(r"training_events", TrainingEventViewSet)
router.register(r"position_groups", PositionGroupViewSet)

# Residents
router.register(r"residents", ResidentsViewSet, basename="residents")
router.register(
    r"residents/(?P<parent_pk>\d+)/archived-1823s",
    ResidentArchived1823sViewSet,
    basename="archived-1823s",
)
router.register(r"resident-bed-holds", ResidentBedHoldViewSet, basename="resident-bed-holds")
router.register(r"cloudcare/residents", CloudCareResidentsViewSet, basename="cloudcare-residents")


# Plans
router.register(r"plans", PlansViewSet, basename="plans")

# Subscriptions
router.register(r"subscriptions", SubscriptionsViewSet, basename="subscriptions")
router.register(r"sponsors", SponsorsViewSet, basename="sponsors")

# Users
router.register(r"users", UsersViewSet, basename="users")

# User Invites
router.register(r"user-invites", UserInvitesViewSet, basename="user-invites")

# Examiners
router.register(r"examiners", ExaminersViewSet, basename="examiners")
router.register(
    r"examination-requests", ExaminationRequestsViewSet, basename="examination-requests"
)

# Course
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r"course-items", CourseItemViewSet, basename="course-items")
router.register(r"course-item-texts", CourseItemTextViewSet, basename="course-item-texts")
router.register(r"course-item-boolean", CourseItemBooleanViewSet, basename="course-item-boolean")
router.register(r"course-item-videos", CourseItemVideoViewSet, basename="course-item-videos")
router.register(
    r"course-item-choices", CourseItemMultiChoiceViewSet, basename="course-item-choices"
)

# Tutorial Videos
router.register(r"tutorial-videos", TutorialVideosViewSet, basename="tutorial-videos")

# Extra shits
extra_patterns = [
    re_path(r"^auth/", include("apps.djoser_alf.urls")),
    re_path(
        r"^continuing-education/facility/(?P<facility_id>\d+)/$",
        ContinuingEducationSummaryForFacilityView.as_view(),
        name="continuing-education-facility",
    ),
    re_path(
        r"^continuing-education/employee/(?P<employee_id>\d+)/$",
        ContinuingEducationSummaryForEmployeeView.as_view(),
        name="continuing-education-employee",
    ),
    re_path(r"^compliance/$", ComplianceView.as_view(), name="compliance"),
    re_path(r"^currentuser/$", CurrentUserView.as_view(), name="currentuser"),
    re_path(
        r"^training_events/(?P<pk>\d+).pdf/$",
        TrainingEventPdfView.as_view(),
        name="trainingevent-flyer",
    ),
    # Dashboard
    re_path(
        r"^upcoming-tasks.pdf/$",
        UpcomingTasksPdfView.as_view(),
        name="upcoming-tasks-pdf",
    ),
    # Employees
    re_path(r"^employees.pdf/$", EmployeesListPdfView.as_view(), name="employees-pdf"),
    re_path(
        r"^employees/(?P<pk>\d+).pdf/$",
        EmployeesDetailPdfView.as_view(),
        name="employees-detail-pdf",
    ),
    re_path(
        r"^employees/(?P<pk>\d+)-certificates.pdf/$",
        EmployeesCertificatesPdfView.as_view(),
        name="employees-certificates-pdf",
    ),
    # Residents
    re_path(r"^residents.pdf/$", ResidentsListPdfView.as_view(), name="residents-pdf"),
    re_path(r"^admissions.pdf/$", ResidentsAdmissionPdfView.as_view(), name="admissions-pdf"),
    re_path(
        r"^residents/(?P<pk>\d+)/facesheet.pdf/$",
        ResidentsFacesheetPdfView.as_view(),
        name="residents-facesheet-pdf",
    ),
    re_path(
        r"^residents/(?P<pk>\d+)/1823.pdf/$",
        Residents1823PdfView.as_view(),
        name="residents-1823-pdf",
    ),
    re_path(
        r"^residents/(?P<pk>\d+)/1823-blank.pdf/$",
        ResidentsBlank1823PdfView.as_view(),
        name="residents-blank-1823-pdf",
    ),
]
urlpatterns = extra_patterns + router.urls
