import logging
from sys import stderr, exit
from typing import Sequence
from pathlib import Path

from common.logging_config import setup_logging
from common.log_paths import get_log_file
from scan_batcher.batch import Batch, Scan
from scan_batcher.parser import Parser
from scan_batcher.workflows import get_workflow
from scan_batcher.workflow import Workflow
from scan_batcher.constants import DEFAULT_ENGINE, RoundingStrategy


def get_subclasses(cls: type) -> list[type]:
    """
    Recursively find all subclasses of a given class, including subclasses of subclasses.

    Args:
        cls (type): The base class to search subclasses for.

    Returns:
        list[type]: List of all subclasses (including nested).
    """
    subclasses = []
    for subclass in cls.__subclasses__():
        subclasses.append(subclass)
        subclasses.extend(get_subclasses(subclass))
    return subclasses

def create_batch(
    batch: Sequence[str] | None, 
    min_res: int | None, 
    max_res: int | None, 
    res_list: Sequence[int] | None, 
    rounding: RoundingStrategy | str
) -> Batch:
    """
    Create a Batch subclass instance based on the input batch type (case-insensitive).
    Supports all direct and indirect subclasses of Batch.

    Args:
        batch (Sequence[str] | None): List where the first element specifies the batch type (e.g., "Scan", "CALCULATE").
        min_res (int | None): Minimum resolution parameter for the batch.
        max_res (int | None): Maximum resolution parameter for the batch.
        res_list (Sequence[int] | None): List of resolutions for processing.
        rounding (RoundingStrategy | str): Rounding method to apply.

    Returns:
        Batch: An instance of the matching Batch subclass (e.g., Scan, Calculate, Process).

    Raises:
        ValueError: If the batch type is unknown or empty (defaults to Scan if batch is empty/None).
    """
    if not batch or batch[0] == "":
        return Scan(min_res, max_res, res_list, rounding)
    
    kind = batch[0].lower()  # Case-insensitive comparison
    
    # Search through all subclasses (including nested)
    for cls in get_subclasses(Batch):
        if cls.__name__.lower() == kind:
            return cls(min_res, max_res, res_list, rounding, *batch[1:])
    
    raise ValueError(f"Unknown batch type: {batch[0]}")

def create_workflow(engine: str = DEFAULT_ENGINE) -> Workflow:
    """
    Get a registered workflow class by engine name and return its instance.

    Args:
        engine (str): The type of engine to create (e.g., "vuescan", "silverfast").

    Returns:
        Workflow: An instance of the Workflow class.

    Raises:
        ValueError: If the workflow is not registered.
    """
    workflow_class = get_workflow(engine)
    return workflow_class()

def main() -> None:
    """
    Main entry point for the CLI utility.

    Initializes logging, parses arguments, creates batch and workflow objects,
    and executes the workflow for each batch item.
    """
    setup_logging(
        log_file=get_log_file("scan_batcher"),
        level=logging.INFO,
        console=True
    )
    logger = logging.getLogger(__name__)
    logger.info("Script has been started")
    
    parser = Parser()
    args = parser.parse_args()
    batch = create_batch(args.batch, args.min_dpi, args.max_dpi, args.dpis, args.rounding)

    workflow = create_workflow(args.engine)
    for item in batch:
        try:
            batch_dict = dict(item) if isinstance(item, list) else item
            templates_dict = dict(args.templates) if args.templates else {}

            if batch_dict:
                merged_templates = {**templates_dict, **batch_dict}
            else:
                merged_templates = {**templates_dict}
            workflow(args.workflow, merged_templates)

        except KeyboardInterrupt:
            logger.info("Script interrupted by user")
            exit(0)
        except Exception as e:
            logger.error(f"Error: {e}")
            stderr.write(f"Error: {e}\n")
            continue

    logger.info("Script has been completed")

if __name__ == "__main__":
    main()
