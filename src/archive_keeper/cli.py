"""Command Line Interface for Archive Keeper."""

import argparse
import logging
import sys
from pathlib import Path

from common.logging_config import setup_logging
from common.log_paths import get_log_file
from .config import Config
from .engine import DatabaseManager
from .scanner import ArchiveScanner

def main() -> None:
    parser = argparse.ArgumentParser(description="Archive Keeper - Digital Preservation Tool")
    parser.add_argument("root_path", help="Root path of the archive to scan")
    parser.add_argument("--config", help="Path to JSON configuration file")
    parser.add_argument("--db", help="Path to SQLite database (overrides config)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--log-dir", help="Custom directory for log files (default: ~/.florentine-abbot/logs/)")
    
    args = parser.parse_args()
    
    setup_logging(
        log_file=get_log_file("archive_keeper", args.log_dir),
        level=logging.DEBUG if args.verbose else logging.INFO,
        console=True
    )
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = Config(args.config)
    logger.info(f"Configuration loaded from {config.config_path}")
    
    # CLI --db parameter overrides config
    db_path = args.db if args.db else config.database
    
    root_path = Path(args.root_path)
    if not root_path.exists():
        logger.error(f"Root path does not exist: {root_path}")
        sys.exit(1)
        
    logger.info(f"Initializing Archive Keeper for {root_path}")
    logger.info(f"Database: {db_path}")
    logger.info(f"Chunk size: {config.chunk_size / (1024*1024):.0f}MB")
    
    # Initialize DB
    db_manager = DatabaseManager(db_path)
    db_manager.init_db()
    
    # Run Scan
    scanner = ArchiveScanner(
        str(root_path), 
        db_manager, 
        chunk_size=config.chunk_size
    )
    try:
        scanner.scan()
    except Exception as e:
        logger.critical(f"Fatal error during scan: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
