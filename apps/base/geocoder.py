import re

from django.conf import settings
from django.contrib.gis.geos import Point

import googlemaps

ALPHA_OR_DIGIT = re.compile(r"[\d|\w]")


def get_geolocation_point(data):
    # Data could be address or zip code
    if settings.ENVIRONMENT == "test" or ALPHA_OR_DIGIT.search(data) is None:
        return None

    gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)
    geocode_result = gmaps.geocode(data)
    if not geocode_result:
        return None
    location = geocode_result[0]["geometry"]["location"]
    return Point(location["lng"], location["lat"])
