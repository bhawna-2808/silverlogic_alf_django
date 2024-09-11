import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from actstream import action
from aweber_api import AWeberAPI
from rest_framework import mixins, viewsets
from rest_framework.decorators import action as action_decorator
from rest_framework.response import Response
import requests
from apps.api.trainings.serializers import EmployeeCreateSerializer
from apps.api.users.serializers import UserSerializer
from apps.trainings.models import Position
import json
from .serializers import EmployeeRegisterSerializer, RegisterSerializer

logger = logging.getLogger(__name__)


class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = RegisterSerializer
    queryset = []

    @transaction.atomic
    def perform_create(self, serializer):
        user_facility = serializer.save()
        self.send_welcome_email(user_facility["user"])
        self.subscribe_to_aweber(user_facility["user"], user_facility["facility"])
        self.create_employee(user_facility["user"], user_facility["facility"])
        self.send_to_monday(user_facility["user"], user_facility["facility"])

        action.send(
            user_facility["user"],
            verb="created facility",
            action_object=user_facility["facility"],
        )
    def send_to_monday(self, user, facility):
        api_Key = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjMzNjMyNDI0MiwiYWFpIjoxMSwidWlkIjoxMTExNTk0OSwiaWFkIjoiMjAyNC0wMy0yMVQyMDozMDoyNS4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6NTAxODY4MCwicmduIjoidXNlMSJ9.0zLMH1Qt_xzxBh845x7HakVo7kblwzob3BvPsl--1DA"
        api_url = "https://api.monday.com/v2"
        headers = {
            "Authorization": api_Key,
            "Content-Type": "application/json",
        }

        query = """
        mutation {
        create_item (
            board_id: 3816422531,
            group_id: "topics",
            item_name: "New Item", # This is the item name; replace it with your desired item name.
            column_values: "{\"name\": \"John Doe\"}" # Replace "John Doe" and "john.doe@example.com" with the desired name and email.
        ) {
            id
        }
        }
        """

        vars = {
            "myItemName": f"{user.first_name} {user.last_name}",
            "columnVals": json.dumps({
                "name": user.first_name,
                "email": {"text": user.email},
                "status": "New Trail",
                # "date": {"date": timezone.now().strftime("%Y-%m-%d")},
                # "text": {"text": user.first_name}
            })
        }

        data = {'query': query, 'variables': vars}

        try:
            r = requests.post(url=api_url, json=data, headers=headers)
            r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send data to Monday.com: {str(e)}")
            
            
    def send_welcome_email(self, user):
        subject = "Welcome to ALFBoss!"
        body = render_to_string(
            "trainings/emails/welcome.txt",
            {"FRONT_URL": settings.FRONT_URL, "username": user.username},
        )
        send_mail(subject, body, from_email=None, recipient_list=[user.email])

    def subscribe_to_aweber(self, user, facility):
        if not hasattr(settings, "AWEBER_CONSUMER_KEY"):
            logger.info("aweber not configured, not subscribing %s", user.email)
            return

        try:
            aweber = AWeberAPI(settings.AWEBER_CONSUMER_KEY, settings.AWEBER_CONSUMER_SECRET)
            account = aweber.get_account(
                settings.AWEBER_ACCESS_TOKEN, settings.AWEBER_ACCESS_SECRET
            )
            for mail_list in account.lists:
                if mail_list.unique_list_id == settings.AWEBER_TRIAL_LIST_ID:
                    break
            else:
                logger.error(
                    "Could not find aweber newsletter with unique id %s",
                    settings.AWEBER_TRIAL_LIST_ID,
                )
                return

            url = "/accounts/{account_id}/lists/{list_id}/subscribers".format(
                account_id=account.id, list_id=mail_list.id
            )
            params = {
                "ws.op": "create",
                "email": user.email,
                "name": "{} {}".format(user.first_name, user.last_name),
                "custom_fields": {"Facility": facility.name},
            }
            account.adapter.request("POST", url, params)
        except Exception as ex:
            logger.exception("error creating aweber subscriber %s", str(ex))

    def create_employee(self, user, facility):
        position, _ = Position.objects.get_or_create(name="Administrator")
        data = {
            **self.request.data.get("employee"),
            "user": user.pk,
            "facility": facility.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "positions": [position.pk],
        }
        context = self.get_serializer_context()
        context["request"].facility = facility
        serializer = EmployeeCreateSerializer(None, data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    @action_decorator(methods=["post"], serializer_class=EmployeeRegisterSerializer, detail=False)
    def employee(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        self.send_welcome_email(data["user"])
        return Response(UserSerializer(instance=data["user"], context={"request": request}).data)
