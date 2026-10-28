#!/usr/bin/env python3
"""CLI: convert .docx files to Markdown."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from converter import collect_docx_files, convert_docx_to_md, default_output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docx_to_md",
        description="將 Word (.docx) 轉成 Markdown (.md)",
    )
    parser.add_argument("input", type=Path, help="輸入的 .docx 檔，或包含多個 .docx 的資料夾")
    parser.add_argument("-o", "--output", type=Path, help="輸出 .md 路徑（僅單檔）")
    parser.add_argument("-d", "--out-dir", type=Path, help="輸出資料夾")
    parser.add_argument("-r", "--recursive", action="store_true", help="遞迴搜尋子目錄")
    parser.add_argument("--no-images", action="store_true", help="不匯出圖片")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        inputs = collect_docx_files([args.input], recursive=args.recursive)
        if not inputs:
            raise FileNotFoundError(f"找不到 .docx：{args.input}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"錯誤: {exc}", file=sys.stderr)
        return 1

    if args.output and len(inputs) > 1:
        print("錯誤: 批次轉換請用 --out-dir", file=sys.stderr)
        return 1

    ok = 0
    failed = 0
    for input_path in inputs:
        output_path = args.output or default_output_path(input_path, args.out_dir)
        try:
            messages = convert_docx_to_md(
                input_path,
                output_path,
                extract_images=not args.no_images,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[失敗] {input_path} -> {exc}", file=sys.stderr)
            failed += 1
            continue

        print(f"[完成] {input_path} -> {output_path}")
        for msg in messages:
            print(f"  警告: {msg}")
        ok += 1

    print(f"\n完成 {ok} 個，失敗 {failed} 個")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
