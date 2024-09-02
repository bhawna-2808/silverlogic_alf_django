import json
import re

from django.utils.functional import cached_property

import requests
from embed_video.backends import VideoBackend, VideoDoesntExistException, YoutubeBackend
from embed_video.settings import EMBED_VIDEO_TIMEOUT


class SecureYoutubeBackend(YoutubeBackend):
    is_secure = True


class SecureWistiaBackend(VideoBackend):
    domain = None
    is_secure = True

    re_detect = re.compile(r"https://(?P<domain>[a-z0-9-]+).wistia.com/medias/*", re.I)
    re_code = re.compile(
        r"""wistia\.com/(medias/(.*/)?|deliveries/)(?P<code>[a-z0-9;:@?&%=+/\$_.-]+)""",
        re.I,
    )

    pattern_url = "{protocol}://fast.wistia.net/embed/iframe/{code}"
    pattern_info = "{protocol}://fast.wistia.net/oembed?url={protocol}%3A%2F%2F{domain}.wistia.com%2Fmedias%2F{code}&embedType=async"

    @cached_property
    def width(self):
        return self.info.get("width")

    @cached_property
    def height(self):
        return self.info.get("height")

    def get_info(self):
        try:
            response = requests.get(
                self.pattern_info.format(
                    domain=self.domain, code=self.code, protocol=self.protocol
                ),
                timeout=EMBED_VIDEO_TIMEOUT,
            )
            return json.loads(response.text)
        except ValueError:
            raise VideoDoesntExistException()

    def get_thumbnail_url(self):
        return self.info.get("thumbnail_url")
