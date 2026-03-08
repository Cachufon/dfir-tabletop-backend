#!/usr/bin/env python3
"""
Export participant-facing TTX handouts (SitMan + Participant Guide) from Markdown to offline HTML.

Inputs:
- A "package directory" produced by build_ttx_package_from_yaml.py containing:
  - sitman.md
  - participant_guide.md

Outputs:
- index.html
- sitman.html
- participant_guide.html
- handouts_html.zip (optional)

SAFETY:
- By default, this script refuses to write outputs inside the git repo directory.
- Use --allow-in-repo ONLY for synthetic examples.

Dependencies:
- markdown (pip package name: markdown)

Install:
  pip install markdown

Example (recommended; secure storage outside git):
  python3 dfir_backend/ttx/scripts/export_ttx_handouts_html.py \
    --package-dir /secure_storage/ttx/<case_id>/20_delivery/ttx_package \
    --out-dir /secure_storage/ttx/<case_id>/20_delivery/ttx_package/handouts_html \
    --zip
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict

try:
    import markdown  # type: ignore
except Exception:
    print("ERROR: Missing dependency 'markdown'. Install with: pip install markdown", file=sys.stderr)
    raise


def repo_root_from_here() -> Path:
    # .../dfir_backend/ttx/scripts/export_ttx_handouts_html.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def md_to_html(md: str) -> str:
    return markdown.markdown(
        md,
        extensions=[
            "tables",
            "fenced_code",
            "toc",
        ],
        output_format="html5",
    )


def page_template(title: str, body_html: str, nav_links: Dict[str, str]) -> str:
    nav = " | ".join([f'<a href="{href}">{label}</a>' for label, href in nav_links.items()])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    :root {{
      --maxw: 980px;
      --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      --sans: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
    }}
    body {{
      font-family: var(--sans);
      margin: 0;
      padding: 0;
      line-height: 1.5;
      color: #111;
      background: #fff;
    }}
    header {{
      border-bottom: 1px solid #e5e7eb;
      padding: 14px 18px;
      background: #fafafa;
    }}
    header .wrap {{
      max-width: var(--maxw);
      margin: 0 auto;
      display: flex;
      gap: 16px;
      align-items: baseline;
      justify-content: space-between;
    }}
    header .nav {{
      font-size: 14px;
      color: #374151;
    }}
    header .nav a {{
      color: #2563eb;
      text-decoration: none;
    }}
    main {{
      max-width: var(--maxw);
      margin: 0 auto;
      padding: 22px 18px 60px;
    }}
    code, pre {{
      font-family: var(--mono);
      font-size: 13px;
    }}
    pre {{
      padding: 12px;
      background: #0b1020;
      color: #e5e7eb;
      overflow-x: auto;
      border-radius: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0 18px;
      font-size: 14px;
    }}
    th, td {{
      border: 1px solid #e5e7eb;
      padding: 8px;
      vertical-align: top;
    }}
    th {{
      background: #f3f4f6;
      text-align: left;
    }}
    .hint {{
      font-size: 13px;
      color: #6b7280;
      margin-top: 6px;
    }}
    @media print {{
      header {{ display: none; }}
      main {{ max-width: none; padding: 0; }}
      a {{ color: #111; text-decoration: none; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <div><strong>TTX Handouts</strong></div>
      <div class="nav">{nav}</div>
    </div>
  </header>
  <main>
    {body_html}
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Export participant-facing TTX handouts to HTML.")
    parser.add_argument("--package-dir", required=True, help="Directory containing sitman.md and participant_guide.md")
    parser.add_argument("--out-dir", required=True, help="Output directory for HTML files")
    parser.add_argument("--zip", action="store_true", help="Also create a handouts_html.zip archive in the output directory")
    parser.add_argument("--allow-in-repo", action="store_true", help="Allow writing outputs inside the git repo (synthetic only)")
    args = parser.parse_args()

    repo_root = repo_root_from_here()

    package_dir = Path(args.package_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    if not package_dir.is_dir():
        print(f"ERROR: package-dir not found or not a directory: {package_dir}", file=sys.stderr)
        return 2

    sitman_md = package_dir / "sitman.md"
    guide_md = package_dir / "participant_guide.md"

    if not sitman_md.exists():
        print(f"ERROR: sitman.md not found in package-dir: {sitman_md}", file=sys.stderr)
        return 2
    if not guide_md.exists():
        print(f"ERROR: participant_guide.md not found in package-dir: {guide_md}", file=sys.stderr)
        return 2

    if not args.allow_in_repo and is_within(out_dir, repo_root):
        print(
            "ERROR: Refusing to write outputs inside the git repo directory.\n"
            f"- Repo root: {repo_root}\n"
            f"- Output dir: {out_dir}\n\n"
            "Write outputs to secure project storage outside git, or use --allow-in-repo ONLY for synthetic examples.",
            file=sys.stderr,
        )
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)

    nav = {"Home": "index.html", "SitMan": "sitman.html", "Participant Guide": "participant_guide.html"}

    index_body = """
<h1>TTX Participant Handouts</h1>
<p class="hint">These handouts are intended for participants. They are offline-friendly and printable.</p>
<ul>
  <li><a href="sitman.html">Situation Manual (SitMan)</a></li>
  <li><a href="participant_guide.html">Participant Guide (Pre-read)</a></li>
</ul>
<p class="hint">If you received these files as a ZIP, extract them and open <code>index.html</code> in a browser.</p>
"""
    write_text(out_dir / "index.html", page_template("TTX Handouts", index_body, nav))

    sitman_html = md_to_html(read_text(sitman_md))
    guide_html = md_to_html(read_text(guide_md))

    write_text(out_dir / "sitman.html", page_template("SitMan", sitman_html, nav))
    write_text(out_dir / "participant_guide.html", page_template("Participant Guide", guide_html, nav))

    if args.zip:
        # Create archive beside the out_dir. Example: /path/handouts_html.zip
        zip_base = out_dir / "handouts_html"
        shutil.make_archive(str(zip_base), "zip", root_dir=str(out_dir))
        print(f"Created ZIP: {zip_base}.zip")

    print("HTML handouts generated:")
    print(f"- {out_dir / 'index.html'}")
    print(f"- {out_dir / 'sitman.html'}")
    print(f"- {out_dir / 'participant_guide.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
