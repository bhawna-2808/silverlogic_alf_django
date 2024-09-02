import base64
import logging
import os
from datetime import datetime
from urllib.request import urlretrieve

from django.conf import settings

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    ContentId,
    Disposition,
    FileContent,
    FileName,
    FileType,
    Mail,
)
from virtru_sdk import Client, EncryptFileParams, Policy

from apps.residents.models import ProviderEmail

logger = logging.getLogger(__name__)


def email_provider_file(
    provider_file,
    provider,
    subject="ALFBoss LTC Resident info",
    html_content="Hi, \n This is an automated email containing the required PHI file.",
):
    try:
        email_to_list = []
        for email in ProviderEmail.objects.filter(provider=provider.pk):
            email_to_list.append(email.email)

        file_out = f'/tmp/{provider.name}_file_{datetime.today().strftime("%Y-%m-%d")}.tdf3.html'
        client = Client(
            owner=settings.VIRTRU_OWNER_ADDRESS,
            api_key=settings.VIRTRU_HMAC,
            secret=settings.VIRTRU_SECRET,
        )
        policy = Policy()
        policy.share_with_users(email_to_list)
        downloaded_provider_file, _ = urlretrieve(provider_file.file.url)  # Grab from S3
        param = EncryptFileParams(in_file_path=downloaded_provider_file, out_file_path=file_out)
        param.set_policy(policy)
        client.encrypt_file(encrypt_file_params=param)

        message = Mail(
            from_email="noreply@alfboss.com",
            to_emails=email_to_list,
            subject=subject,
            html_content=html_content,
        )
        with open(file_out, "rb") as f:
            data = f.read()
            f.close()
        encoded = base64.b64encode(data).decode()
        attachment = Attachment()
        attachment.file_content = FileContent(encoded)
        attachment.file_type = FileType("application/octet-stream")
        attachment.file_name = FileName(f"{file_out.replace('/tmp/', '')}")
        attachment.disposition = Disposition("attachment")
        attachment.content_id = ContentId("PHI")
        message.attachment = attachment
        sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sendgrid_client.send(message)
        logger.info(f"Email sent to {email_to_list} with status {response.status_code}")
    except Exception as e:
        logger.error(e.message)
    finally:
        os.remove(file_out)
