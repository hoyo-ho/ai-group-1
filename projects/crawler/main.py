# -*- coding: utf-8 -*-
"""
Crawler CLI Entry Point
"""
import argparse
import sys
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.crawler import crawl
from src.config import OUTPUT_DIR, DOWNLOADS_DIR, EXPORT_FORMATS


def main():
    parser = argparse.ArgumentParser(
        description="Universal Web Crawler - Extract content from websites"
    )
    parser.add_argument("url", nargs="?", default=None, help="URL to crawl")
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
        choices=["wiki", "baike", "baidu", "bilibili", "douyin", "sohu", "quark", "quora", "csdn", "cnblogs", "juejin", "segmentfault", "github", "gitee", "zhihu", "stackoverflow", "trafilatura", "general"],
        default=None,
        help="Specify site type for extraction (auto-detected if not provided)"
    )
    parser.add_argument(
        "--batch", "-b",
        type=str,
        default=None,
        help="Batch crawl URLs from a file (one URL per line)"
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        default=None,
        help="Multiple URLs to crawl (space-separated)"
    )
    parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=1,
        help="Number of concurrent crawls (default: 1)"
    )
    
    args = parser.parse_args()
    
    if args.list_formats:
        print("Supported export formats:")
        for fmt in EXPORT_FORMATS:
            print(f"  - {fmt}")
        return
    
    # Collect URLs
    urls = []
    if args.batch:
        # Read URLs from file
        batch_file = Path(args.batch)
        if batch_file.exists():
            with open(batch_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        else:
            print(f"Error: Batch file not found: {args.batch}")
            sys.exit(1)
    elif args.urls:
        urls = args.urls
    elif args.url:
        urls = [args.url]
    else:
        print("Error: Please provide URL, --urls, or --batch")
        parser.print_help()
        sys.exit(1)
    
    if not urls:
        print("Error: No URLs provided")
        sys.exit(1)
    
    # Determine output directory
    output_dir = DOWNLOADS_DIR if args.dir == "downloads" else OUTPUT_DIR
    
    # Batch crawl function
    def crawl_one(url, idx):
        filename = f"{args.output}_{idx}" if args.output else None
        return crawl(
            url=url,
            formats=args.formats,
            filename=filename,
            output_dir=output_dir,
            use_playwright=args.playwright,
            site_type=args.site
        )
    
    # Run crawl(s)
    if len(urls) == 1:
        # Single URL mode
        print(f"Crawling: {urls[0]}")
        print(f"Export formats: {', '.join(args.formats)}")
        print(f"Output directory: {output_dir}")
        if args.site:
            print(f"Site type: {args.site} (forced)")
        else:
            print(f"Site type: auto-detect")
        print("-" * 50)
        
        result = crawl_one(urls[0], 0)
        
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
    else:
        # Batch mode
        print(f"Batch crawling {len(urls)} URLs")
        print(f"Export formats: {', '.join(args.formats)}")
        print(f"Concurrency: {args.concurrency}")
        print("-" * 50)
        
        results = []
        if args.concurrency > 1:
            # Concurrent mode
            with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = {executor.submit(crawl_one, url, idx): url for idx, url in enumerate(urls)}
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        print(f"✅ {url}")
                    except Exception as e:
                        print(f"❌ {url}: {e}")
        else:
            # Sequential mode
            for idx, url in enumerate(urls):
                print(f"[{idx+1}/{len(urls)}] Crawling: {url}")
                try:
                    result = crawl_one(url, idx)
                    results.append(result)
                    print(f"✅ Completed: {url}")
                except Exception as e:
                    print(f"❌ Failed: {url} - {e}")
        
        # Summary
        success_count = sum(1 for r in results if "error" not in r)
        print("\n" + "=" * 50)
        print(f"📊 Batch Summary: {success_count}/{len(urls)} successful")


if __name__ == "__main__":
    main()
