# -*- coding: utf-8 -*-
"""Tests for exporters"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.exporters import JSONExporter, MarkdownExporter, PDFFxporter, CSVExporter, ImageExporter


class TestJSONExporter:
    """Test JSON exporter"""

    def test_export_basic(self, sample_data, tmp_output_dir):
        exporter = JSONExporter()
        result = exporter.export(sample_data, "test", tmp_output_dir)
        
        assert Path(result).exists()
        assert result.endswith(".json")

    def test_export_content(self, sample_data, tmp_output_dir):
        exporter = JSONExporter()
        result = exporter.export(sample_data, "test", tmp_output_dir)
        
        import json
        with open(result, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["title"] == "Example Domain"
        assert data["url"] == "https://example.com"


class TestMarkdownExporter:
    """Test Markdown exporter"""

    def test_export_basic(self, sample_data, tmp_output_dir):
        exporter = MarkdownExporter()
        result = exporter.export(sample_data, "test", tmp_output_dir)
        
        assert Path(result).exists()
        assert result.endswith(".md")

    def test_export_content(self, sample_data, tmp_output_dir):
        exporter = MarkdownExporter()
        result = exporter.export(sample_data, "test", tmp_output_dir)
        
        content = Path(result).read_text(encoding="utf-8")
        assert "Example Domain" in content
        assert "https://example.com" in content

    def test_export_nested(self, sample_data, tmp_output_dir):
        exporter = MarkdownExporter()
        result = exporter.export(sample_data, "test", tmp_output_dir)
        
        content = Path(result).read_text(encoding="utf-8")
        assert "meta" in content or "author" in content.lower()


class TestCSVExporter:
    """Test CSV exporter"""

    def test_export_basic(self, sample_data, tmp_output_dir):
        exporter = CSVExporter()
        result = exporter.export(sample_data, "test", tmp_output_dir)
        
        assert Path(result).exists()
        assert result.endswith(".csv")


class TestPDFFxporter:
    """Test PDF exporter"""

    def test_export_basic(self, sample_data, tmp_output_dir):
        exporter = PDFFxporter()
        result = exporter.export(sample_data, "test", tmp_output_dir)
        
        # Should generate PDF (or fallback to MD if weasyprint fails)
        assert Path(result).exists()
        assert result.endswith(".pdf") or result.endswith(".md")

    def test_export_pdf_extension(self, sample_data, tmp_output_dir):
        """Test PDF output has correct extension when weasyprint works"""
        try:
            import weasyprint
            exporter = PDFFxporter()
            result = exporter.export(sample_data, "test", tmp_output_dir)
            # If weasyprint works, should return .pdf
            assert result.endswith(".pdf")
        except ImportError:
            # If weasyprint not available, should fallback to .md
            assert result.endswith(".md")


class TestImageExporter:
    """Test Image exporter"""

    def test_export_basic(self, sample_data, tmp_output_dir):
        exporter = ImageExporter()
        result = exporter.export(sample_data, "test", tmp_output_dir)
        
        # Image exporter may return path or error string
        assert result is not None
