from datetime import datetime, timedelta

from django.utils.timezone import utc


def get_timestamp(target_datetime):
    return int(
        (target_datetime - datetime(1970, 1, 1, tzinfo=utc)).total_seconds()
        / timedelta(seconds=1).total_seconds()
    )
