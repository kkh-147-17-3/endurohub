import re

import nh3


# Allowed tags for rich text content
ALLOWED_TAGS = {
    'p', 'br', 'strong', 'em', 'u', 's',
    'h2', 'h3',
    'ul', 'ol', 'li',
    'blockquote',
    'a',
    'pre', 'code',
    'span',   # text color
    'mark',   # highlight
    'img',    # inline images
}

# Allowed attributes per tag
# Note: 'a' rel is handled by link_rel parameter, not listed here
ALLOWED_ATTRIBUTES = {
    'a': {'href', 'target'},
    'span': {'style'},
    'mark': {'data-color', 'style'},
    'img': {'src', 'alt', 'title', 'width'},
}

# Only allow safe URL schemes
ALLOWED_URL_SCHEMES = {'http', 'https', 'mailto'}

# Regex to validate style attributes
COLOR_STYLE_RE = re.compile(r'^color:\s*#[0-9a-fA-F]{3,6}\s*;?\s*$')
BG_COLOR_STYLE_RE = re.compile(
    r'^background-color:\s*#[0-9a-fA-F]{3,6}\s*;?\s*$'
)

# Regex for safe img src (internal uploads only)
SAFE_IMG_SRC_RE = re.compile(r'^/storage/posts/inline/\d{4}-\d{2}/[a-zA-Z0-9]+\.\w+$')

# Simple HTML tag regex for text extraction
HTML_TAG_RE = re.compile(r'<[^>]+>')


def _attribute_filter(tag: str, name: str, value: str) -> str | None:
    """Filter attributes to only allow safe values."""
    if tag == 'a':
        if name == 'href':
            # Block javascript: and data: URLs
            lower_val = value.lower().strip()
            if lower_val.startswith(('javascript:', 'data:', 'vbscript:')):
                return None
            return value
        if name == 'target':
            return '_blank'
        if name == 'rel':
            return 'nofollow noopener noreferrer'
        return None

    if tag == 'span':
        if name == 'style':
            # Only allow color property
            if COLOR_STYLE_RE.match(value):
                return value
            return None
        return None

    if tag == 'mark':
        if name == 'data-color':
            # Allow hex color values
            if re.match(r'^#[0-9a-fA-F]{3,6}$', value):
                return value
            return None
        if name == 'style':
            # Only allow background-color
            if BG_COLOR_STYLE_RE.match(value):
                return value
            return None
        return None

    if tag == 'img':
        if name == 'src':
            # Only allow internal storage paths
            if SAFE_IMG_SRC_RE.match(value):
                return value
            return None
        if name in ('alt', 'title'):
            return value
        if name == 'width':
            # Only allow numeric width values
            if value.isdigit():
                return value
            return None
        return None

    return value


def sanitize_html(html: str) -> str:
    """
    Sanitize HTML content, keeping only allowed tags and attributes.
    Forces safe rel on links and blocks dangerous URLs.
    """
    if not html:
        return ''

    cleaned = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        attribute_filter=_attribute_filter,
        link_rel='nofollow noopener noreferrer',
    )

    return cleaned


def html_to_text(html: str) -> str:
    """Strip all HTML tags and return plain text."""
    if not html:
        return ''
    text = HTML_TAG_RE.sub('', html)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
