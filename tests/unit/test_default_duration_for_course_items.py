import pytest
from faker import Faker

import tests.factories as f

pytestmark = pytest.mark.django_db
fake = Faker()


def test_default_duration_for_text_items():
    text = f.CourseItemTextFactory(question=fake.text(), answer=fake.text())
    item = text.item
    text2 = f.CourseItemTextFactory(question=fake.text(), answer=fake.text(), item=item)

    assert item.min_duration is None
    item.save()
    words = len(
        text.question.split() + text.answer.split() + text2.question.split() + text2.answer.split()
    )
    assert item.min_duration == words / item.AVERAGE_WORDS_PER_SECOND


@pytest.mark.parametrize(
    "item_factory",
    [
        f.CourseItemBooleanFactory,
        f.CourseItemMultiChoiceFactory,
        f.CourseItemLetterSizeImageFactory,
    ],
)
def test_default_duration_for_other_items(item_factory):
    section = item_factory()
    item = section.item
    item_factory(item=item)

    assert item.min_duration is None
    item.save()
    assert item.min_duration == item.DEFAULT_DURATION * 2


def test_default_duration_for_video_items():
    video = f.CourseItemVideoFactory()
    item = video.item

    assert item.min_duration is None
    item.save()
    assert item.min_duration == item.DEFAULT_DURATION


def test_default_duration_for_banner(image_django_file):
    item = f.CourseItemFactory()

    assert item.min_duration is None
    item.image = image_django_file
    item.save()
    assert item.min_duration == item.DEFAULT_DURATION
