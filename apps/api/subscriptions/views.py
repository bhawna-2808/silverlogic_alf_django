import logging
from datetime import date

from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

import stripe
from actstream import action
from django_fsm import can_proceed
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action as action_decorator
from rest_framework.response import Response

from apps.subscriptions.models import Sponsor, Subscription

from ..mixins import DestroyModelMixin
from ..permissions import IsAuthenticated, IsSameFacility, IsSameFacilityForEditing
from .serializers import SponsorsSerializer, SubscriptionSerializer, SubscriptionTrialSerializer

logger = logging.getLogger(__name__)


class SubscriptionsViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated, IsSameFacilityForEditing]

    def get_queryset(self):
        queryset = super(SubscriptionsViewSet, self).get_queryset()
        queryset = queryset.filter(facility=self.request.facility)
        return queryset

    def perform_destroy(self, instance):
        if not can_proceed(instance.cancel):
            raise serializers.ValidationError(
                {"non_field_errors": [_("The subscription has already been deleted.")]}
            )
        try:
            instance.cancel()
        except stripe.error.StripeError:
            logger.exception("stripe error during subscription cancellation")
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "An error occurred while cancelling your subscription, please try again later."
                        )
                    ]
                }
            )
        instance.save()

    def send_ebook(self, request):
        user = request.user
        context = {"user": user}
        subject = render_to_string("api/emails/ebook-subject.txt", context).strip()
        message = render_to_string("api/emails/ebook-body.txt", context)
        html_message = render_to_string("api/emails/ebook-body.html", context)
        email = EmailMultiAlternatives(subject, message, from_email=None, to=[user.email])
        email.attach_alternative(html_message, "text/html")
        email.send()

    @action_decorator(methods=["GET"], detail=False)
    def current(self, request):
        module = request.GET.get("module", "resident")
        subscription = (
            Subscription.objects.current()
            .filter(facility=request.facility, billing_interval__plan__module=module)
            .first()
        )
        if not subscription:
            return Response({})
        return Response(self.get_serializer(instance=subscription).data)

    @action_decorator(methods=["GET"], detail=False)
    def currents(self, request):
        subscriptions = Subscription.objects.current().filter(facility=request.facility)
        return Response(self.get_serializer(subscriptions, many=True).data)

    @action_decorator(methods=["POST"], serializer_class=SubscriptionTrialSerializer, detail=False)
    def start_trial(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        action.send(
            self.request.user,
            verb="started trial subscription",
            action_object=subscription,
            target=subscription.facility,
        )

        if "ebook" in serializer.validated_data and serializer.validated_data["ebook"]:
            self.send_ebook(request)
            request.facility.bought_ebook = True
            request.facility.save()

        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        instance = serializer.save()
        action.send(
            self.request.user,
            verb="started subscription",
            action_object=instance,
            target=instance.facility,
        )


class SponsorsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Sponsor.objects.all()
    serializer_class = SponsorsSerializer
    permission_classes = [IsAuthenticated, IsSameFacility]

    def get_queryset(self):
        today = date.today()
        queryset = super().get_queryset()
        return queryset.filter(
            Q(sponsorhips__end_date__gte=today) | Q(sponsorhips__end_date__isnull=True),
            sponsorhips__facility=self.request.facility,
            sponsorhips__start_date__lte=today,
            sponsorhips__facility__opted_in_sponsorship_date__lte=today,
            sponsorhips__facility__sponsored_access=True,
        )
