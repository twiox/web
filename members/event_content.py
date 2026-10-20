"""Event descriptions written with Editor.js: checking the saved blocks and turning them into HTML.

The editor stores {"blocks": [{"type": ..., "data": {...}}, ...]}. Texts may contain
inline HTML (bold, italic, links). It is filtered with nh3 when the event is saved
and again when it is shown, so nothing else ever reaches the page.
"""
import html
import os

import nh3
from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html, format_html_join, strip_tags
from django.utils.safestring import mark_safe

HEADER_LEVELS = (2, 3, 4)
LIST_STYLES = ("unordered", "ordered", "checklist")
# Editor.js counter types -> CSS list-style-type
COUNTER_TYPES = {
    "numeric": "decimal",
    "lower-roman": "lower-roman",
    "upper-roman": "upper-roman",
    "lower-alpha": "lower-alpha",
    "upper-alpha": "upper-alpha",
}
MAX_LIST_DEPTH = 5

INVALID = "Die Beschreibung konnte nicht gelesen werden."


def clean_inline(text):
    """Keeps bold, italic, line breaks and links; removes every other tag and attribute."""
    if not isinstance(text, str):
        raise ValidationError(INVALID)
    return nh3.clean(
        text,
        tags={"b", "i", "a", "br"},
        attributes={"a": {"href"}},
        url_schemes={"http", "https", "mailto", "tel"},
        link_rel="noopener noreferrer",
        set_tag_attribute_values={"a": {"target": "_blank"}},
    )


def _plain(text):
    """Text without any markup, for attributes like alt."""
    return html.unescape(strip_tags(text or ""))


## Saving
def _clean_list_items(items, style, depth=1):
    if not isinstance(items, list) or depth > MAX_LIST_DEPTH:
        raise ValidationError(INVALID)
    cleaned = []
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError(INVALID)
        meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
        cleaned.append({
            "content": clean_inline(item.get("content", "")),
            "meta": {"checked": bool(meta.get("checked"))} if style == "checklist" else {},
            "items": _clean_list_items(item.get("items", []), style, depth + 1),
        })
    return cleaned


def _clean_list(data):
    style = data.get("style") if data.get("style") in LIST_STYLES else "unordered"
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    clean_meta = {}
    if style == "ordered":
        if isinstance(meta.get("start"), int) and meta["start"] > 0:
            clean_meta["start"] = meta["start"]
        if meta.get("counterType") in COUNTER_TYPES:
            clean_meta["counterType"] = meta["counterType"]
    return {"style": style, "meta": clean_meta, "items": _clean_list_items(data.get("items"), style)}


def _clean_block(kind, data, asset):
    if kind == "paragraph":
        return {"text": clean_inline(data.get("text", ""))}
    if kind == "header":
        level = data.get("level") if data.get("level") in HEADER_LEVELS else HEADER_LEVELS[0]
        return {"text": clean_inline(data.get("text", "")), "level": level}
    if kind == "list":
        return _clean_list(data)
    if kind == "quote":
        alignment = "center" if data.get("alignment") == "center" else "left"
        return {
            "text": clean_inline(data.get("text", "")),
            "caption": clean_inline(data.get("caption", "")),
            "alignment": alignment,
        }
    if kind == "delimiter":
        return {}
    if kind == "image":
        return {
            "file": {"url": asset.file.url},
            "caption": clean_inline(data.get("caption", "")),
            "withBorder": False,
            "withBackground": False,
            "stretched": False,
        }
    if kind == "attaches":
        return {
            "file": {
                "url": asset.file.url,
                "name": asset.name,
                "size": asset.file.size,
                "extension": os.path.splitext(asset.name)[1].lstrip(".").lower(),
            },
            "title": clean_inline(data.get("title", "")) or asset.name,
        }
    raise ValidationError(f"Unbekannter Baustein „{kind}“ in der Beschreibung.")


def clean_content(data, assets):
    """Checks and filters the editor output.

    assets maps file URLs to the uploads this event may use.
    Returns the cleaned content and the uploads it references.
    """
    if not isinstance(data, dict) or not isinstance(data.get("blocks"), list):
        raise ValidationError(INVALID)
    blocks, used = [], []
    for block in data["blocks"]:
        if not isinstance(block, dict) or not isinstance(block.get("data"), dict):
            raise ValidationError(INVALID)
        kind, values = block.get("type"), block["data"]
        asset = None
        if kind in ("image", "attaches"):
            file = values.get("file") if isinstance(values.get("file"), dict) else {}
            asset = assets.get(file.get("url"))
            if asset is None or asset.kind != ("image" if kind == "image" else "file"):
                raise ValidationError(
                    "Ein Bild oder eine Datei in der Beschreibung wurde nicht gefunden. Bitte erneut hochladen."
                )
            used.append(asset)
        cleaned = {"type": kind, "data": _clean_block(kind, values, asset)}
        if isinstance(block.get("id"), str):
            cleaned["id"] = block["id"][:20]
        blocks.append(cleaned)
    return {"blocks": blocks}, used


## Showing
def _inline(text):
    return mark_safe(clean_inline(text if isinstance(text, str) else ""))


def _media_url(file):
    url = file.get("url", "") if isinstance(file, dict) else ""
    return url if url.startswith(settings.MEDIA_URL) else None


def _render_list_items(items, style):
    rows = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        checked = style == "checklist" and (item.get("meta") or {}).get("checked")
        nested = item.get("items")
        rows.append(format_html(
            '<li{}>{}{}</li>',
            mark_safe(' class="checked"') if checked else "",
            _inline(item.get("content")),
            _render_list(nested, style, {}) if nested else "",
        ))
    return mark_safe("".join(rows))


def _render_list(items, style, meta):
    if style == "ordered":
        return format_html(
            '<ol start="{}" style="list-style-type: {}">{}</ol>',
            meta.get("start") if isinstance(meta.get("start"), int) else 1,
            COUNTER_TYPES.get(meta.get("counterType"), "decimal"),
            _render_list_items(items, style),
        )
    css = ' class="event_content__checklist"' if style == "checklist" else ""
    return format_html("<ul{}>{}</ul>", mark_safe(css), _render_list_items(items, style))


def _render_block(block):
    if not isinstance(block, dict) or not isinstance(block.get("data"), dict):
        return ""
    kind, data = block.get("type"), block["data"]
    if kind == "paragraph":
        return format_html("<p>{}</p>", _inline(data.get("text")))
    if kind == "header":
        level = data.get("level") if data.get("level") in HEADER_LEVELS else HEADER_LEVELS[0]
        return format_html("<h{0}>{1}</h{0}>", level, _inline(data.get("text")))
    if kind == "list":
        meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
        return _render_list(data.get("items"), data.get("style"), meta)
    if kind == "quote":
        caption = data.get("caption")
        return format_html(
            '<blockquote class="event_content__quote{}"><p>{}</p>{}</blockquote>',
            " event_content__quote--center" if data.get("alignment") == "center" else "",
            _inline(data.get("text")),
            format_html("<cite>{}</cite>", _inline(caption)) if caption else "",
        )
    if kind == "delimiter":
        return mark_safe('<hr class="event_content__delimiter">')
    if kind == "image" and (url := _media_url(data.get("file"))):
        caption = data.get("caption")
        return format_html(
            '<figure class="event_content__image"><img src="{}" alt="{}" loading="lazy">{}</figure>',
            url,
            _plain(caption),
            format_html("<figcaption>{}</figcaption>", _inline(caption)) if caption else "",
        )
    if kind == "attaches" and (url := _media_url(data.get("file"))):
        file = data["file"]
        details = [str(file.get("extension", "")).upper()]
        if isinstance(file.get("size"), int):
            details.append(filesizeformat(file["size"]))
        return format_html(
            '<a class="event_content__file download" href="{}" target="_blank" rel="noopener">'
            "<span>{}<small>{}</small></span><i class=\"fas fa-file-download\"></i></a>",
            url,
            _inline(data.get("title") or file.get("name")),
            " · ".join(d for d in details if d),
        )
    return ""


def render_content(content):
    """HTML for the saved blocks; unknown or broken blocks are skipped."""
    blocks = content.get("blocks") if isinstance(content, dict) else None
    if not isinstance(blocks, list):
        return ""
    return format_html_join("", "{}", ((_render_block(block),) for block in blocks))
