from rest_framework import mixins, response, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.api.trainings.serializers import EmployeeReadSerializer, VerifyInviteSerializer

from .serializers import LoginSerializer


class LoginViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = LoginSerializer
    queryset = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.save()
        return response.Response({"token": token.key})

    @action(methods=["post"], serializer_class=VerifyInviteSerializer, detail=False)
    def verify(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        resp = EmployeeReadSerializer(instance=employee)
        return Response(resp.data)
