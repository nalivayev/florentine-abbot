"""Command Line Interface for Archive Organizer."""

import argparse
import logging
import sys
from pathlib import Path

from .processor import ArchiveProcessor
from .monitor import ArchiveMonitor
from .config import Config

def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main() -> None:
    parser = argparse.ArgumentParser(
        description="File Organizer - Metadata Extraction and Organization Tool",
        epilog="Use --config to specify a JSON configuration file with metadata settings."
    )
    parser.add_argument("input_path", help="Path to the folder to process or monitor")
    parser.add_argument("--watch", action="store_true", help="Run in daemon mode (watch for new files)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--config", help="Path to JSON configuration file (see config.template.json)")

    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    input_path = Path(args.input_path)
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)

    # Load configuration
    config = Config(args.config)
    metadata = config.get_metadata()

    if args.watch:
        logger.info(f"Starting Archive Organizer in WATCH mode on {input_path}")
        monitor = ArchiveMonitor(str(input_path), config)
        monitor.start()
    else:
        logger.info(f"Starting Archive Organizer in BATCH mode on {input_path}")
        processor = ArchiveProcessor()
        
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
