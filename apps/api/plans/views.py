from rest_framework import mixins, viewsets

from apps.subscriptions.models import Plan

from .serializers import PlanSerializer


class PlansViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
