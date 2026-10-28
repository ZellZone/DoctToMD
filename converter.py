#!/usr/bin/env python3
"""DOCX → Markdown conversion core."""

from __future__ import annotations

import re
from pathlib import Path

import mammoth
from markdownify import markdownify as html_to_md


DOCX_SUFFIXES = {".docx"}


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\-]+", "-", name, flags=re.UNICODE).strip("-").lower()
    return slug or "image"


def _make_image_converter(media_dir: Path, media_rel: str):
    counter = {"n": 0}

    def convert_image(image):
        counter["n"] += 1
        ext = (image.content_type or "image/png").split("/")[-1]
        if ext == "jpeg":
            ext = "jpg"

        alt = image.alt_text or f"image-{counter['n']}"
        filename = f"{counter['n']:03d}-{_slugify(alt)}.{ext}"
        media_dir.mkdir(parents=True, exist_ok=True)
        out_path = media_dir / filename

        with image.open() as img_file:
            out_path.write_bytes(img_file.read())

        return {"src": f"{media_rel}/{filename}".replace("\\", "/")}

    return convert_image


def convert_docx_to_md(
    input_path: Path,
    output_path: Path,
    *,
    extract_images: bool = True,
) -> list[str]:
    """Convert one .docx file to Markdown. Returns warning messages."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    convert_kwargs = {}
    if extract_images:
        media_dir = output_path.with_name(f"{output_path.stem}_media")
        media_rel = media_dir.name
        convert_kwargs["convert_image"] = mammoth.images.img_element(
            _make_image_converter(media_dir, media_rel)
        )

    with input_path.open("rb") as docx_file:
        result = mammoth.convert_to_html(docx_file, **convert_kwargs)

    markdown = (
        html_to_md(
            result.value,
            heading_style="ATX",
            bullets="-",
            strong_em_symbol="*",
            strip=["script", "style"],
        ).strip()
        + "\n"
    )

    output_path.write_text(markdown, encoding="utf-8")
    return [str(msg) for msg in result.messages]


def collect_docx_files(paths: list[Path], *, recursive: bool = False) -> list[Path]:
    """Collect unique .docx files from files and/or folders."""
    found: list[Path] = []

    for path in paths:
        if path.is_file():
            if path.suffix.lower() in DOCX_SUFFIXES:
                found.append(path.resolve())
            continue

        if path.is_dir():
            pattern = "**/*.docx" if recursive else "*.docx"
            found.extend(p.resolve() for p in path.glob(pattern) if p.is_file())

    return sorted(set(found))


def default_output_path(input_path: Path, out_dir: Path | None = None) -> Path:
    if out_dir is not None:
        return out_dir / f"{input_path.stem}.md"
    return input_path.with_suffix(".md")
