from datetime import timedelta

from django.http import HttpResponse
from django.utils import timezone

import pytest
from rest_framework import permissions
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.api.authentication import TrainingsTimedAuthTokenAuthentication
from apps.facilities.models import FacilityUser, TrainingsTimedAuthToken

import tests.factories as f
import tests.helpers as h
from tests.mixins import ApiMixin

pytestmark = pytest.mark.django_db


class MockView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = [TrainingsTimedAuthTokenAuthentication]

    def get(self, request):
        return HttpResponse({"a": 1, "b": 2, "c": 3})


class TestTrainingsTimedAuthToken(ApiMixin):
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.view = MockView.as_view()
        self.factory = APIRequestFactory()

    @pytest.mark.parametrize(
        "role",
        [
            FacilityUser.Role.account_admin,
            FacilityUser.Role.trainings_user,
            FacilityUser.Role.manager,
        ],
    )
    def test_trainings_user_tokens_never_expire(self, role):
        trainings_user = f.TrainingsUserFactory()

        token = TrainingsTimedAuthToken.objects.create(user=trainings_user.user)
        token.expires = timezone.now() - timedelta(weeks=100)
        token.save()

        request = self.factory.get("/test/", HTTP_AUTHORIZATION="Token {}".format(token.key))
        request.facility_user = f.FacilityUserFactory(role=role, user=trainings_user.user)
        request.facility = request.facility_user.facility

        r = self.view(request)
        h.responseOk(r)

    @pytest.mark.parametrize("role", [FacilityUser.Role.examiner])
    def test_normal_tokens_expire(self, role):
        examiner = f.ExaminerFactory()

        token = TrainingsTimedAuthToken.objects.create(user=examiner.user)
        token.expires = timezone.now() - timedelta(weeks=100)
        token.save()

        request = self.factory.get("/test/", HTTP_AUTHORIZATION="Token {}".format(token.key))
        request.facility_user = f.FacilityUserFactory(role=role, user=examiner.user)
        request.facility = request.facility_user.facility

        r = self.view(request)
        h.responseUnauthorized(r)
        assert r.data["detail"] == "Token has expired"
