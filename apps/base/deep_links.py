import logging

from django.conf import settings

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def get_deep_link(
    fallback_url=None,
    for_ios=False,
    for_android=False,
    for_windows_phone=False,
    for_blackberry=False,
    for_fire=False,
    **kwargs,
):
    """
    Create Branch.io deep link
    Valid params and return value can be found at:
    https://github.com/BranchMetrics/branch-deep-linking-public-api#creating-a-deep-linking-url
    """
    kwargs["branch_key"] = settings.BRANCHIO_KEY
    kwargs["data"] = {}

    if fallback_url:
        kwargs["data"]["$desktop_url"] = fallback_url
        if not for_ios:
            kwargs["data"]["$ios_url"] = fallback_url
        if not for_android:
            kwargs["data"]["$android_url"] = fallback_url
        if not for_windows_phone:
            kwargs["data"]["$windows_phone_url"] = fallback_url
        if not for_blackberry:
            kwargs["data"]["$blackberry_url"] = fallback_url
        if not for_fire:
            kwargs["data"]["$fire_url"] = fallback_url
    try:
        r = requests.post("https://api.branch.io/v1/url", json=kwargs)
        r.raise_for_status()
    except RequestException:
        logger.error("Could not generate deep link for employee ID:  %s", kwargs.get("employee"))
        return settings.BRANCHIO_FALLBACK_URL
    else:
        return r.json()["url"]
