import re

_IMAGE_TAG_PATTERN = re.compile(r"<img\b", re.IGNORECASE)


def source_contains_image_tag(text: str) -> bool:
    return _IMAGE_TAG_PATTERN.search(text) is not None