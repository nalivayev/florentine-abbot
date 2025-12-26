"""Command Line Interface for Archive Keeper."""

import argparse
import logging
import sys
from pathlib import Path

from common.logger import Logger
from archive_keeper.config import Config
from archive_keeper.engine import DatabaseManager
from archive_keeper.scanner import ArchiveScanner

def main() -> None:
    parser = argparse.ArgumentParser(description="Archive Keeper - Digital Preservation Tool")
    parser.add_argument("root_path", help="Root path of the archive to scan")
    parser.add_argument("--config", help="Path to JSON configuration file")
    parser.add_argument("--db", help="Path to SQLite database (overrides config)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--log-path", help="Custom directory for log files (default: ~/.florentine-abbot/logs/)")
    
    args = parser.parse_args()
    
    logger = Logger(
        "archive_keeper", 
        args.log_path,
        level=logging.DEBUG if args.verbose else logging.INFO,
        console=True
    )
    
    # Load configuration
    config = Config(logger, args.config)
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
        logger,
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
