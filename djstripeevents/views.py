import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Event
from .signals import event_received


class StripeWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            event = Event.objects.get(stripe_id=request.data["id"])
        except Event.DoesNotExist:
            event = Event()
            event.stripe_id = request.data["id"]
        event.type = request.data["type"]
        event.created = datetime.datetime.utcfromtimestamp(request.data["created"])
        event.data = request.data["data"]
        event.request = request.data["request"] or ""
        event.pending_webhooks = request.data["pending_webhooks"]
        event.save()

        event_received.send(sender="djstripeevents", event=event)

        return Response({})
