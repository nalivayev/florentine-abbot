"""Command Line Interface for Archive Keeper."""

import argparse
import logging
import sys
from pathlib import Path

from .engine import DatabaseManager
from .scanner import ArchiveScanner

def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("archive_keeper.log")
        ]
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Archive Keeper - Digital Preservation Tool")
    parser.add_argument("root_path", help="Root path of the archive to scan")
    parser.add_argument("--db", default="archive.db", help="Path to SQLite database (default: archive.db)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    root_path = Path(args.root_path)
    if not root_path.exists():
        logger.error(f"Root path does not exist: {root_path}")
        sys.exit(1)
        
    logger.info(f"Initializing Archive Keeper for {root_path}")
    
    # Initialize DB
    db_manager = DatabaseManager(args.db)
    db_manager.init_db()
    
    # Run Scan
    scanner = ArchiveScanner(str(root_path), db_manager)
    try:
        scanner.scan()
    except Exception as e:
        logger.critical(f"Fatal error during scan: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
