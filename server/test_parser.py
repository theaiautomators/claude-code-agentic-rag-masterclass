"""
Tests for the document parser module.
Verifies parsing of PDF, DOCX, HTML, Markdown, and TXT formats.
"""
import pytest
from pathlib import Path
from parser import parse_document

# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"


class TestParseDocument:
    """Test cases for parse_document function."""

    def test_parse_txt_file(self):
        """Test parsing a plain text file."""
        # Create a test txt file
        test_file = TEST_DATA_DIR / "test_parse.txt"
        test_file.write_text("This is test content for parsing.")
        
        content = parse_document(str(test_file))
        
        assert isinstance(content, str)
        assert len(content) > 0
        assert "test content" in content
        
        # Cleanup
        test_file.unlink()

    def test_parse_md_file(self):
        """Test parsing a Markdown file."""
        file_path = TEST_DATA_DIR / "sample.md"
        content = parse_document(str(file_path))
        
        assert isinstance(content, str)
        assert len(content) > 0
        # Docling parses markdown and retains structure
        assert "Markdown Document" in content

    def test_parse_html_file(self):
        """Test parsing an HTML file."""
        file_path = TEST_DATA_DIR / "sample.html"
        content = parse_document(str(file_path))
        
        assert isinstance(content, str)
        assert len(content) > 0
        # Docling parses HTML and extracts text content
        assert "HTML Document" in content

    def test_parse_pdf_file(self):
        """Test parsing a PDF file."""
        file_path = TEST_DATA_DIR / "sample.pdf"
        content = parse_document(str(file_path))
        
        assert isinstance(content, str)
        assert len(content) > 0

    def test_parse_docx_file(self):
        """Test parsing a DOCX file."""
        file_path = TEST_DATA_DIR / "sample.docx"
        content = parse_document(str(file_path))
        
        assert isinstance(content, str)
        assert len(content) > 0
        # Docling parses DOCX and retains structure
        assert "Word Document" in content

    def test_unsupported_format_raises_error(self):
        """Test that unsupported file formats raise a clear error."""
        # Create a temporary file with unsupported extension
        fake_file = TEST_DATA_DIR / "fake.xyz"
        fake_file.write_text("dummy content")
        
        with pytest.raises(ValueError) as excinfo:
            parse_document(str(fake_file))
        
        assert "Unsupported file format" in str(excinfo.value)
        assert ".xyz" in str(excinfo.value)
        
        # Cleanup
        fake_file.unlink()

    def test_nonexistent_file_raises_error(self):
        """Test that nonexistent files raise an appropriate error."""
        nonexistent = TEST_DATA_DIR / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            parse_document(str(nonexistent))

    def test_case_insensitive_extension(self):
        """Test that file extensions are handled case-insensitively."""
        # Create a file with uppercase extension
        upper_file = TEST_DATA_DIR / "test.TXT"
        upper_file.write_text("Test content")
        
        content = parse_document(str(upper_file))
        assert content == "Test content"
        
        # Cleanup
        upper_file.unlink()

    def test_returns_string_type(self):
        """Test that parse_document always returns a string."""
        # Create a test txt file
        test_file = TEST_DATA_DIR / "test_string.txt"
        test_file.write_text("Hello World")
        
        content = parse_document(str(test_file))
        
        assert isinstance(content, str)
        
        # Cleanup
        test_file.unlink()

    def test_empty_txt_file(self):
        """Test parsing an empty text file."""
        empty_file = TEST_DATA_DIR / "empty.txt"
        empty_file.write_text("")
        
        content = parse_document(str(empty_file))
        
        assert content == ""
        
        # Cleanup
        empty_file.unlink()
