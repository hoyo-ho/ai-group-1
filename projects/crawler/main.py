# -*- coding: utf-8 -*-
"""
Crawler CLI Entry Point
"""
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.crawler import crawl
from src.config import OUTPUT_DIR, DOWNLOADS_DIR, EXPORT_FORMATS


def main():
    parser = argparse.ArgumentParser(
        description="Universal Web Crawler - Extract content from websites"
    )
    parser.add_argument("url", help="URL to crawl")
    parser.add_argument(
        "-f", "--formats",
        nargs="+",
        choices=EXPORT_FORMATS,
        default=["json"],
        help=f"Export formats (default: json). Available: {', '.join(EXPORT_FORMATS)}"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output filename (without extension)"
    )
    parser.add_argument(
        "-d", "--dir",
        type=str,
        choices=["output", "downloads"],
        default="output",
        help="Output directory: 'output' (project folder) or 'downloads' (~/Downloads)"
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List supported export formats"
    )
    parser.add_argument(
        "--playwright", "-p",
        action="store_true",
        help="Use Playwright for JavaScript-rendered pages"
    )
    parser.add_argument(
        "--site",
        type=str,
        choices=["wiki", "baike", "baidu", "bilibili", "douyin", "sohu", "quark", "general"],
        default=None,
        help="Specify site type for extraction (auto-detected if not provided)"
    )
    
    args = parser.parse_args()
    
    if args.list_formats:
        print("Supported export formats:")
        for fmt in EXPORT_FORMATS:
            print(f"  - {fmt}")
        return
    
    # Determine output directory
    output_dir = DOWNLOADS_DIR if args.dir == "downloads" else OUTPUT_DIR
    
    print(f"Crawling: {args.url}")
    print(f"Export formats: {', '.join(args.formats)}")
    print(f"Output directory: {output_dir}")
    if args.site:
        print(f"Site type: {args.site} (forced)")
    else:
        print(f"Site type: auto-detect")
    print("-" * 50)
    
    # Run crawler
    result = crawl(
        url=args.url,
        formats=args.formats,
        filename=args.output,
        output_dir=output_dir,
        use_playwright=args.playwright,
        site_type=args.site
    )
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    # Print results
    print("\n✅ Crawl completed!")
    print(f"\nTitle: {result['content'].get('title', 'N/A')}")
    print(f"URL: {result['url']}")
    
    if result['content'].get('images'):
        print(f"Images found: {len(result['content']['images'])}")
    
    print("\n📁 Exported files:")
    for fmt, path in result.get("exports", {}).items():
        if path and not path.startswith("ERROR"):
            print(f"  [{fmt}] {path}")
        else:
            print(f"  [{fmt}] {path}")


if __name__ == "__main__":
    main()
