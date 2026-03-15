# -*- coding: utf-8 -*-
"""
Content Exporters
"""
import json
import csv
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from .config import OUTPUT_DIR, DOWNLOADS_DIR


class BaseExporter:
    """Base exporter"""
    
    def export(self, data: Dict, filename: str, output_dir: Path = None) -> str:
        raise NotImplementedError
    
    def _get_output_path(self, filename: str, output_dir: Path = None) -> Path:
        """Get output file path"""
        if output_dir is None:
            output_dir = OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / filename


class JSONExporter(BaseExporter):
    """Export to JSON format"""
    
    def export(self, data: Dict, filename: str, output_dir: Path = None) -> str:
        filepath = self._get_output_path(filename, output_dir)
        if not filepath.suffix:
            filepath = filepath.with_suffix(".json")
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)


class CSVExporter(BaseExporter):
    """Export to CSV format"""
    
    def export(self, data: Dict, filename: str, output_dir: Path = None) -> str:
        filepath = self._get_output_path(filename, output_dir)
        if not filepath.suffix:
            filepath = filepath.with_suffix(".csv")
        
        # Flatten data for CSV
        flat_data = self._flatten_data(data)
        
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            if flat_data:
                writer = csv.DictWriter(f, fieldnames=flat_data[0].keys())
                writer.writeheader()
                writer.writerows(flat_data)
        
        return str(filepath)
    
    def _flatten_data(self, data: Dict) -> List[Dict]:
        """Flatten nested data for CSV"""
        result = []
        
        def flatten(obj, parent_key=""):
            items = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_key = f"{parent_key}.{k}" if parent_key else k
                    if isinstance(v, (dict, list)):
                        items.extend(flatten(v, new_key))
                    else:
                        items.append((new_key, v))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    items.extend(flatten(item, f"{parent_key}[{i}]"))
            else:
                items.append((parent_key, obj))
            return items
        
        flat = dict(flatten(data))
        if flat:
            result.append(flat)
        
        return result


class MarkdownExporter(BaseExporter):
    """Export to Markdown format"""
    
    def export(self, data: Dict, filename: str, output_dir: Path = None) -> str:
        filepath = self._get_output_path(filename, output_dir)
        if not filepath.suffix:
            filepath = filepath.with_suffix(".md")
        
        content = self._build_markdown(data)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(filepath)
    
    def _build_markdown(self, data: Dict, level: int = 1) -> str:
        """Build markdown content"""
        md = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                md.append(f"{'#' * level} {key}\n")
                md.append(self._build_markdown(value, level + 1))
            elif isinstance(value, list):
                md.append(f"{'#' * level} {key}\n")
                for item in value:
                    if isinstance(item, dict):
                        md.append(self._build_markdown(item, level + 1))
                    else:
                        md.append(f"- {item}\n")
                    md.append("\n")
            else:
                md.append(f"{'#' * level} {key}: {value}\n")
        
        return "".join(md)


class PDFFxporter(BaseExporter):
    """Export to PDF format (via markdown conversion)"""
    
    def export(self, data: Dict, filename: str, output_dir: Path = None) -> str:
        # First export as markdown
        md_exporter = MarkdownExporter()
        md_path = md_exporter.export(data, filename, output_dir)
        
        # Note: Actual PDF conversion would require weasyprint or similar
        # For now, return the markdown file path
        return md_path


class ImageExporter(BaseExporter):
    """Export images (download and save)"""
    
    def export(self, data: Dict, filename: str, output_dir: Path = None, source_url: str = None) -> str:
        if output_dir is None:
            output_dir = OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        images = data.get("images", [])
        if not images:
            return ""
        
        downloaded = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        # Add Referer to bypass hotlink protection
        if source_url:
            headers["Referer"] = source_url
        
        for i, img in enumerate(images):
            img_url = img.get("url", "")
            if not img_url:
                continue
            
            # Determine extension
            ext = Path(img_url).suffix or ".jpg"
            img_filename = f"{filename}_{i}{ext}" if filename else f"image_{i}{ext}"
            img_path = output_dir / img_filename
            
            try:
                import requests
                response = requests.get(img_url, timeout=30, headers=headers)
                response.raise_for_status()
                
                with open(img_path, "wb") as f:
                    f.write(response.content)
                
                downloaded.append(str(img_path))
            except Exception as e:
                print(f"Failed to download {img_url}: {e}")
        
        return ",".join(downloaded) if downloaded else ""


def get_exporter(format_type: str) -> BaseExporter:
    """Get exporter by format type"""
    exporters = {
        "json": JSONExporter(),
        "csv": CSVExporter(),
        "markdown": MarkdownExporter(),
        "md": MarkdownExporter(),
        "pdf": PDFFxporter(),
        "png": ImageExporter(),
        "jpg": ImageExporter(),
        "jpeg": ImageExporter(),
    }
    
    return exporters.get(format_type.lower())


def export_content(data: Dict, formats: List[str], filename: str = None, output_dir: Path = None, source_url: str = None) -> Dict[str, str]:
    """Export content to multiple formats"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawl_{timestamp}"
    
    results = {}
    
    for fmt in formats:
        try:
            exporter = get_exporter(fmt)
            if exporter:
                # Pass source_url only for image exporters
                if isinstance(exporter, ImageExporter):
                    output_path = exporter.export(data, filename, output_dir, source_url)
                else:
                    output_path = exporter.export(data, filename, output_dir)
                results[fmt] = output_path
        except Exception as e:
            results[fmt] = f"ERROR: {str(e)}"
    
    return results
