"""Command Line Interface for Archive Organizer."""

import argparse
import logging
import sys
from pathlib import Path

from common.logger import Logger
from file_organizer.processor import ArchiveProcessor
from file_organizer.monitor import ArchiveMonitor
from file_organizer.config import Config

def main() -> None:
    parser = argparse.ArgumentParser(
        description="File Organizer - Metadata Extraction and Organization Tool",
        epilog="Use --config to specify a JSON configuration file with metadata settings."
    )
    parser.add_argument("input_path", help="Path to the folder to process or monitor")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode (monitor for new files)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--config", help="Path to JSON configuration file (see config.template.json)")
    parser.add_argument("--log-path", help="Custom directory for log files (default: ~/.florentine-abbot/logs/)")

    args = parser.parse_args()
    
    logger = Logger(
        "file_organizer", 
        args.log_path,
        level=logging.DEBUG if args.verbose else logging.INFO,
        console=True
    )
    
    input_path = Path(args.input_path)
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)

    # Load configuration
    config = Config(logger, args.config)
    metadata = config.get_metadata()

    if args.daemon:
        logger.info(f"Starting Archive Organizer in DAEMON mode on {input_path}")
        monitor = ArchiveMonitor(logger, str(input_path), config)
        monitor.start()
    else:
        logger.info(f"Starting Archive Organizer in BATCH mode on {input_path}")
        processor = ArchiveProcessor(logger)
        
        # Process existing files
        count = 0
        for file_path in input_path.iterdir():
            if file_path.is_file():
                if processor.should_process(file_path):
                    if processor.process(file_path, metadata):
                        count += 1
        
        logger.info(f"Batch processing complete. Processed {count} files.")

if __name__ == "__main__":
    main()
