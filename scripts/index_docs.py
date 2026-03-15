#!/usr/bin/env python3
"""
Batch document indexing script for RAG system.

Recursively scans docs/, knowledge-base/, and project directories,
ingesting all supported file types (.pdf, .docx, .md, .txt) into
the Supabase pgvector RAG system.

Usage:
    python scripts/index_docs.py [--project PROJECT_NAME] [--force]

Args:
    --project: Optional project name to assign all documents to.
    --force: Re-ingest all files even if content hash is unchanged.
"""

import argparse
import sys
from pathlib import Path
from typing import List

# Add server directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
SERVER_DIR = SCRIPT_DIR.parent / "server"
sys.path.insert(0, str(SERVER_DIR))

from main import ingest_file


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}
DEFAULT_DIRECTORIES = ["docs", "knowledge-base"]


def find_files(base_dirs: List[str], extensions: set) -> List[Path]:
    """
    Recursively find all files with supported extensions.

    Args:
        base_dirs: List of directory names to search (relative to repo root).
        extensions: Set of file extensions to match (e.g., {".md", ".txt"}).

    Returns:
        List of absolute Path objects for all matching files.
    """
    repo_root = SCRIPT_DIR.parent
    found_files = []

    for dir_name in base_dirs:
        dir_path = repo_root / dir_name
        if not dir_path.exists():
            print(f"⚠️  Directory not found: {dir_path}")
            continue

        for ext in extensions:
            matches = list(dir_path.rglob(f"*{ext}"))
            found_files.extend(matches)
            print(f"📁 Found {len(matches)} {ext} file(s) in {dir_name}/")

    return found_files


def index_documents(
    files: List[Path],
    project: str | None = None,
    force: bool = False,
    create_project: bool = False,
) -> dict:
    """
    Ingest all files into the RAG system.

    Args:
        files: List of file paths to ingest.
        project: Optional project name to assign all documents to.
        force: Re-ingest even if content hash is unchanged.
        create_project: Auto-create project if it doesn't exist.

    Returns:
        Summary dict with counts and status per file.
    """
    results = {
        "total": len(files),
        "ingested": 0,
        "skipped": 0,
        "failed": 0,
        "files": [],
    }

    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Processing: {file_path.name}")

        try:
            result = ingest_file(
                str(file_path),
                force=force,
                project=project,
                create_project=create_project,
            )

            status = result.get("status", "unknown")
            results["files"].append({
                "path": str(file_path),
                "status": status,
                "details": result,
            })

            if status in ("completed", "project_confirmation_needed"):
                results["ingested"] += 1
                print(f"   ✅ {status}")
            elif status == "skipped":
                results["skipped"] += 1
                reason = result.get("reason", "unknown")
                print(f"   ⏭️  Skipped ({reason})")
            else:
                results["failed"] += 1
                error_msg = result.get("message", "unknown error")
                print(f"   ❌ Failed: {error_msg}")

        except Exception as e:
            results["failed"] += 1
            results["files"].append({
                "path": str(file_path),
                "status": "error",
                "error": str(e),
            })
            print(f"   ❌ Exception: {e}")

    return results


def print_summary(results: dict):
    """Print ingestion summary."""
    print("\n" + "=" * 60)
    print("📊 INDEXING SUMMARY")
    print("=" * 60)
    print(f"Total files scanned:    {results['total']}")
    print(f"Successfully ingested:  {results['ingested']}")
    print(f"Skipped (duplicate):    {results['skipped']}")
    print(f"Failed:                 {results['failed']}")
    print("=" * 60)

    if results['failed'] > 0:
        print("\n❌ Failed files:")
        for file_result in results['files']:
            if file_result.get('status') in ('error', 'failed'):
                print(f"  - {file_result['path']}")
                if 'error' in file_result:
                    print(f"    Error: {file_result['error']}")
                elif 'details' in file_result:
                    print(f"    Message: {file_result['details'].get('message', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch index documents for RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/index_docs.py
  python scripts/index_docs.py --project my-project
  python scripts/index_docs.py --force
  python scripts/index_docs.py --project my-project --force
        """,
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Project name to assign all documents to",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-ingest all files even if content hash is unchanged",
    )
    parser.add_argument(
        "--create-project",
        action="store_true",
        default=False,
        help="Auto-create project if it doesn't exist",
    )
    parser.add_argument(
        "--dirs",
        type=str,
        nargs="+",
        default=DEFAULT_DIRECTORIES,
        help=f"Directories to scan (default: {' '.join(DEFAULT_DIRECTORIES)})",
    )

    args = parser.parse_args()

    print("🔍 Scanning for documents...")
    files = find_files(args.dirs, SUPPORTED_EXTENSIONS)

    if not files:
        print("ℹ️  No supported files found. Exiting.")
        print_summary({"total": 0, "ingested": 0, "skipped": 0, "failed": 0, "files": []})
        sys.exit(0)

    print(f"\n📚 Found {len(files)} file(s) to index")
    if args.project:
        print(f"   Project: {args.project}")
    if args.force:
        print(f"   Force mode: enabled")

    print("\n🚀 Starting batch ingestion...")
    results = index_documents(
        files,
        project=args.project,
        force=args.force,
        create_project=args.create_project,
    )

    print_summary(results)

    # Exit with error code if any failures
    if results['failed'] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
