"""
Tests for the batch document indexing script (index_docs.py).

Tests cover:
- File discovery across directories
- Supported extension filtering
- Integration with ingest_file
- Summary reporting
- Command-line argument parsing
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add repo root to path so scripts/ and server/ are importable
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.index_docs import (
    find_files,
    index_documents,
    print_summary,
    main,
    SUPPORTED_EXTENSIONS,
    DEFAULT_DIRECTORIES,
)


class TestFindFiles:
    """Test file discovery functionality."""

    def test_find_files_returns_list_of_paths(self, tmp_path):
        """Verify find_files returns a list of Path objects."""
        # Create test directory structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").touch()
        (docs_dir / "readme.txt").touch()

        result = find_files([str(docs_dir)], {".md", ".txt"})

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(p, Path) for p in result)

    def test_find_files_filters_by_extension(self, tmp_path):
        """Verify only supported extensions are found."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "file.md").touch()
        (docs_dir / "file.txt").touch()
        (docs_dir / "file.pdf").touch()
        (docs_dir / "file.py").touch()  # Should be excluded

        result = find_files([str(docs_dir)], {".md", ".txt", ".pdf"})

        assert len(result) == 3
        assert all(p.suffix in {".md", ".txt", ".pdf"} for p in result)

    def test_find_files_recursive_search(self, tmp_path):
        """Verify recursive search finds nested files."""
        docs_dir = tmp_path / "docs"
        subdir = docs_dir / "subdir" / "nested"
        subdir.mkdir(parents=True)
        (docs_dir / "root.md").touch()
        (subdir / "nested.md").touch()

        result = find_files([str(docs_dir)], {".md"})

        assert len(result) == 2
        file_names = [p.name for p in result]
        assert "root.md" in file_names
        assert "nested.md" in file_names

    def test_find_files_skips_missing_directory(self, tmp_path, capsys):
        """Verify missing directories are handled gracefully."""
        nonexistent = tmp_path / "nonexistent"

        result = find_files([str(nonexistent)], {".md"})

        assert result == []
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_find_files_with_multiple_directories(self, tmp_path):
        """Verify multiple directories are searched."""
        docs_dir = tmp_path / "docs"
        kb_dir = tmp_path / "knowledge-base"
        docs_dir.mkdir()
        kb_dir.mkdir()
        (docs_dir / "doc1.md").touch()
        (kb_dir / "doc2.md").touch()

        result = find_files([str(docs_dir), str(kb_dir)], {".md"})

        assert len(result) == 2


class TestIndexDocuments:
    """Test document indexing functionality."""

    @patch('scripts.index_docs.ingest_file')
    def test_index_documents_ingests_all_files(self, mock_ingest, tmp_path):
        """Verify all files are passed to ingest_file."""
        mock_ingest.return_value = {"status": "completed", "document_id": "test-id"}

        files = [tmp_path / "file1.md", tmp_path / "file2.txt"]
        for f in files:
            f.touch()

        results = index_documents(files)

        assert mock_ingest.call_count == 2
        assert results["ingested"] == 2
        assert results["failed"] == 0

    @patch('scripts.index_docs.ingest_file')
    def test_index_documents_handles_skipped_files(self, mock_ingest, tmp_path):
        """Verify skipped files are counted correctly."""
        mock_ingest.return_value = {"status": "skipped", "reason": "duplicate"}

        files = [tmp_path / "file.md"]
        (tmp_path / "file.md").touch()

        results = index_documents(files)

        assert results["skipped"] == 1
        assert results["ingested"] == 0

    @patch('scripts.index_docs.ingest_file')
    def test_index_documents_handles_failed_files(self, mock_ingest, tmp_path):
        """Verify failed files are counted and reported."""
        mock_ingest.return_value = {"status": "error", "message": "File not found"}

        files = [tmp_path / "file.md"]
        (tmp_path / "file.md").touch()

        results = index_documents(files)

        assert results["failed"] == 1
        assert results["files"][0]["status"] == "error"

    @patch('scripts.index_docs.ingest_file')
    def test_index_documents_passes_project_parameter(self, mock_ingest, tmp_path):
        """Verify project parameter is passed to ingest_file."""
        mock_ingest.return_value = {"status": "completed"}

        files = [tmp_path / "file.md"]
        (tmp_path / "file.md").touch()

        index_documents(files, project="test-project")

        mock_ingest.assert_called_once()
        call_kwargs = mock_ingest.call_args[1]
        assert call_kwargs["project"] == "test-project"

    @patch('scripts.index_docs.ingest_file')
    def test_index_documents_passes_force_parameter(self, mock_ingest, tmp_path):
        """Verify force parameter is passed to ingest_file."""
        mock_ingest.return_value = {"status": "completed"}

        files = [tmp_path / "file.md"]
        (tmp_path / "file.md").touch()

        index_documents(files, force=True)

        call_kwargs = mock_ingest.call_args[1]
        assert call_kwargs["force"] is True

    @patch('scripts.index_docs.ingest_file')
    def test_index_documents_handles_exception(self, mock_ingest, tmp_path):
        """Verify exceptions during ingestion are caught."""
        mock_ingest.side_effect = Exception("Connection error")

        files = [tmp_path / "file.md"]
        (tmp_path / "file.md").touch()

        results = index_documents(files)

        assert results["failed"] == 1
        assert results["files"][0]["status"] == "error"


class TestPrintSummary:
    """Test summary reporting functionality."""

    def test_print_summary_shows_counts(self, capsys):
        """Verify summary displays correct counts."""
        results = {
            "total": 10,
            "ingested": 7,
            "skipped": 2,
            "failed": 1,
            "files": [],
        }

        print_summary(results)
        captured = capsys.readouterr()

        assert "10" in captured.out
        assert "7" in captured.out
        assert "2" in captured.out
        assert "1" in captured.out

    def test_print_summary_shows_failed_files(self, capsys):
        """Verify failed files are listed in summary."""
        results = {
            "total": 3,
            "ingested": 2,
            "skipped": 0,
            "failed": 1,
            "files": [
                {"path": "/path/to/failed.md", "status": "error", "error": "File not found"},
            ],
        }

        print_summary(results)
        captured = capsys.readouterr()

        assert "Failed files:" in captured.out
        assert "failed.md" in captured.out


class TestMain:
    """Test command-line interface."""

    @patch('scripts.index_docs.find_files')
    @patch('scripts.index_docs.index_documents')
    def test_main_with_no_files(self, mock_index, mock_find, capsys):
        """Verify graceful exit when no files found."""
        mock_find.return_value = []
        mock_index.return_value = {"total": 0, "ingested": 0, "skipped": 0, "failed": 0, "files": []}

        with patch.object(sys, 'argv', ['index_docs.py']):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0

    @patch('scripts.index_docs.find_files')
    @patch('scripts.index_docs.index_documents')
    def test_main_passes_project_arg(self, mock_index, mock_find, tmp_path):
        """Verify --project argument is passed through."""
        mock_find.return_value = [tmp_path / "test.md"]
        mock_index.return_value = {"total": 1, "ingested": 1, "skipped": 0, "failed": 0, "files": []}

        with patch.object(sys, 'argv', ['index_docs.py', '--project', 'my-project']):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        mock_index.assert_called_once()
        call_kwargs = mock_index.call_args[1]
        assert call_kwargs["project"] == "my-project"

    @patch('scripts.index_docs.find_files')
    @patch('scripts.index_docs.index_documents')
    def test_main_passes_force_arg(self, mock_index, mock_find, tmp_path):
        """Verify --force argument is passed through."""
        mock_find.return_value = [tmp_path / "test.md"]
        mock_index.return_value = {"total": 1, "ingested": 1, "skipped": 0, "failed": 0, "files": []}

        with patch.object(sys, 'argv', ['index_docs.py', '--force']):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        call_kwargs = mock_index.call_args[1]
        assert call_kwargs["force"] is True

    @patch('scripts.index_docs.find_files')
    @patch('scripts.index_docs.index_documents')
    def test_main_exits_with_error_on_failure(self, mock_index, mock_find, tmp_path):
        """Verify exit code 1 when ingestion fails."""
        mock_find.return_value = [tmp_path / "test.md"]
        mock_index.return_value = {"total": 1, "ingested": 0, "skipped": 0, "failed": 1, "files": []}

        with patch.object(sys, 'argv', ['index_docs.py']):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1


class TestSupportedExtensions:
    """Test extension constants."""

    def test_supported_extensions_includes_pdf(self):
        """Verify .pdf is supported."""
        assert ".pdf" in SUPPORTED_EXTENSIONS

    def test_supported_extensions_includes_docx(self):
        """Verify .docx is supported."""
        assert ".docx" in SUPPORTED_EXTENSIONS

    def test_supported_extensions_includes_md(self):
        """Verify .md is supported."""
        assert ".md" in SUPPORTED_EXTENSIONS

    def test_supported_extensions_includes_txt(self):
        """Verify .txt is supported."""
        assert ".txt" in SUPPORTED_EXTENSIONS


class TestDefaultDirectories:
    """Test default directory constants."""

    def test_default_directories_includes_docs(self):
        """Verify docs is in default directories."""
        assert "docs" in DEFAULT_DIRECTORIES

    def test_default_directories_includes_knowledge_base(self):
        """Verify knowledge-base is in default directories."""
        assert "knowledge-base" in DEFAULT_DIRECTORIES
