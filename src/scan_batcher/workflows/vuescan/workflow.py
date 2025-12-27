from configparser import ConfigParser, ExtendedInterpolation
from shutil import SameFileError, move
from os.path import getmtime
from getpass import getuser
from subprocess import run
from pathlib import Path
from re import finditer
from os import makedirs
import datetime

from common.exifer import Exifer
from common.logger import Logger
from scan_batcher.workflows import register_workflow
from scan_batcher.workflow import Workflow
from scan_batcher.constants import EXIF_SUPPORTED_EXTENSIONS, EXIF_DATETIME_FORMAT


@register_workflow("vuescan")
class VuescanWorkflow(Workflow):
    """
    Workflow manager for VueScan scanning operations.

    Handles the complete workflow from configuration to file management
    for VueScan operations, including template processing and EXIF data handling.
    """

    _VUESCAN_SETTINGS_NAME = "vuescan.ini"
    _WORKFLOW_SETTINGS_NAME = "workflow.ini"
    _EXIF_TEMPLATE_NAMES = [
        "digitization_year",
        "digitization_month",
        "digitization_day",
        "digitization_hour",
        "digitization_minute",
        "digitization_second"
    ]
    
    # EXIF tag names for reading date information
    _EXIF_DATE_TAGS = [
        "ExifIFD:DateTimeDigitized",
        "ExifIFD:DateTimeOriginal",
        "ExifIFD:CreateDate",
        "IFD0:DateTime"
    ]

    def __init__(self, logger: Logger) -> None:
        """Initialize the VueScan workflow.
        
        Args:
            logger: Logger instance for this workflow.
        """
        super().__init__()
        self.logger = logger

    def _read_settings_file(self, path: Path) -> ConfigParser:
        """
        Read and parse a configuration file.

        Args:
            path (Path): Path to the configuration file to read.

        Returns:
            ConfigParser: Instance with loaded configuration.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        if path.exists():
            self.logger.info(f"Loading settings from '{str(path)}'")
            parser = ConfigParser(interpolation=ExtendedInterpolation())
            parser.read(path)
            self.logger.info("Settings loaded")
            return parser
        else:
            raise FileNotFoundError(f"Error loading settings from file '{path}'")

    def _add_system_templates(self) -> None:
        """
        Add system-provided templates (like current username) to the templates dictionary.
        """
        self._templates["user_name"] = getuser()

    def _read_settings(self) -> None:
        """
        Read both script and workflow configuration files and initialize parsers.
        """
        self._script_parser = self._read_settings_file(Path(Path(__file__).parent, self._VUESCAN_SETTINGS_NAME))
        self._workflow_parser = self._read_settings_file(Path(self._workflow_path, self._WORKFLOW_SETTINGS_NAME))
        self.logger.info(f"Workflow description: {self._get_workflow_value('main', 'description')}")

    def _get_workflow_value(self, section: str, key: str) -> str:
        """
        Get a value from workflow configuration with template substitution.

        Args:
            section (str): Configuration section name.
            key (str): Key within the section.

        Returns:
            str: The configuration value with all templates resolved.
        """
        value = self._workflow_parser[section][key]
        return self._replace_templates_to_value(value)

    def _get_script_value(self, section: str, key: str) -> str:
        """
        Get a value from script configuration with template substitution.

        Args:
            section (str): Configuration section name.
            key (str): Key within the section.

        Returns:
            str: The configuration value with all templates resolved.
        """
        value = self._script_parser[section][key]
        return self._replace_templates_to_value(value)

    def _overwrite_vuescan_settings_file(self) -> None:
        """
        Generate and overwrite VueScan settings file based on workflow configuration.

        Raises:
            RuntimeError: If there's an error writing the file.
        """
        parser = ConfigParser()
        parser.add_section("VueScan")
        for section in self._workflow_parser.sections():
            if section.startswith("vuescan."):
                vuescan_section = section.split(".")[-1]
                if not parser.has_section(vuescan_section):
                    parser.add_section(vuescan_section)
                items = self._workflow_parser.items(section)
                for item in items:
                    parser[vuescan_section][item[0]] = self._get_workflow_value(section, item[0])
        path = Path(self._get_script_value("main", "settings_path"), self._get_script_value("main", "settings_name"))
        try:
            with open(path, "w") as file:
                parser.write(file)
        except (SameFileError, OSError) as e:
            raise RuntimeError("Error overwriting the VueScan settings file") from e
        self.logger.info(f"VueScan settings file '{path}' overwritten")

    def _run_vuescan(self) -> None:
        """
        Execute the VueScan program with configured settings.

        Raises:
            FileNotFoundError: If VueScan executable is not found.
        """
        program_path = Path(
            self._get_script_value("main", "program_path"), self._get_script_value("main", "program_name")
        )
        if program_path.exists():
            output_path_name = self._get_workflow_value("vuescan", "output_path")
            if not Path(output_path_name).exists():
                makedirs(output_path_name, True)
            self.logger.info(f"Launching VueScan from '{program_path}'")
            run([program_path], cwd=self._get_script_value("main", "program_path"), shell=False)
            self.logger.info("VueScan is closed")
        else:
            raise FileNotFoundError(f"File '{program_path}' not found")

    def _convert_value(self, value: str) -> str:
        """
        Convert a template string to its actual value using the templates dictionary.

        Args:
            value (str): Template string to convert (e.g., "{key:length:alignment:placeholder}").

        Returns:
            str: Formatted string with the template replaced by its actual value.

        Raises:
            KeyError: If template key not found.
            ValueError: If template format is invalid.
        """
        fields = value.split(":")
        if len(fields) > 0:
            key = fields[0]
            try:
                value = self._templates[key]
            except KeyError:
                raise KeyError(f"Key '{key}' not found")
            try:
                length = int(fields[1]) if len(fields) > 1 else 0
                alignment = fields[2] if len(fields) > 2 and fields[2] in ("<", ">", "^") else "<"
                placeholder = fields[3] if len(fields) > 3 else ""
                result = f"{{:{placeholder}{alignment}{length}s}}"
                result = result.format(str(value))
                return result
            except ValueError as e:
                raise ValueError("Template conversion error") from e
        else:
            raise ValueError("An empty template was found")

    def _replace_templates_to_value(self, string: str) -> str:
        """
        Replace all templates in a string with their corresponding values.

        Args:
            string (str): String containing template placeholders.

        Returns:
            str: String with all templates replaced by their values.
        """
        result = string
        for match in finditer("{(.+?)}", string):
            template = string[match.start():match.end()]
            try:
                value = self._convert_value(template[1:-1])
            except (KeyError, ValueError):
                self.logger.warning(f"Error converting template '{string[1:-1]}' to value")
                continue
            result = result.replace(template, value)
        return result

    def _add_output_file_templates(self, path: Path) -> None:
        """
        Extract EXIF data from scanned file and add datetime templates.

        Args:
            path (Path): Path to the scanned file.
        """
        moment = None
        if path.suffix.lower() in EXIF_SUPPORTED_EXTENSIONS:
            try:
                tool = Exifer()
                tags = tool.read(path, self._EXIF_DATE_TAGS)
                
                # Try to get date from any of the tags (in priority order)
                for tag_name in self._EXIF_DATE_TAGS:
                    value = tags.get(tag_name)
                    if value:
                        try:
                            moment = self._parse_exif_datetime(value)
                            break
                        except ValueError:
                            pass
            except Exception as e:
                self.logger.warning(f"Unable to extract EXIF from file '{path.name}': {e}")

        if moment is None:
            moment = datetime.datetime.fromtimestamp(getmtime(path))

        if moment:
            for key in self._EXIF_TEMPLATE_NAMES:
                self._templates[key] = getattr(moment, key.replace("digitization_", ""), "")

    @staticmethod
    def _parse_exif_datetime(value: str) -> datetime.datetime:
        """Parse EXIF datetime string (YYYY:MM:DD HH:MM:SS) to datetime object.
        
        Args:
            value: EXIF datetime string.
            
        Returns:
            Parsed datetime object.
            
        Raises:
            ValueError: If the value cannot be parsed.
        """
        try:
            return datetime.datetime.strptime(value, EXIF_DATETIME_FORMAT)
        except ValueError as e:
            raise ValueError(f"Invalid EXIF datetime format: {value}") from e

    def _move_output_file(self) -> None:
        """
        Move the scanned file from VueScan output to final destination.

        Raises:
            FileNotFoundError: If output file not found.
            RuntimeError: If file move fails.
        """
        input_path = Path(
            self._get_workflow_value("vuescan", "output_path"),
            f"{self._get_workflow_value('vuescan', 'output_file_name')}.{self._get_workflow_value('vuescan', 'output_extension_name')}"
        )
        if input_path.exists():
            self._add_output_file_templates(input_path)
            output_path_name = self._get_workflow_value("main", "output_path")
            if not Path(output_path_name).exists():
                makedirs(output_path_name, True)
            output_path = Path(
                output_path_name,
                f"{self._get_workflow_value('main', 'output_file_name')}{input_path.suffix}"
            )
            try:
                move(input_path, output_path)
                self.logger.info(
                    f"Scanned file '{input_path.name}' moved from '{input_path.parent}' to '{output_path.parent}', "
                    f"final name: '{output_path.name}'"
                )
            except OSError as e:
                raise RuntimeError(
                    f"Error moving resulting file from '{input_path}' to '{output_path}'"
                ) from e
        else:
            self.logger.error(f"Output file '{input_path}' not found after scanning")
            raise FileNotFoundError(f"Output file '{input_path}' not found")

    def _move_logging_file(self) -> None:
        """
        Move VueScan log file to the output directory.
        """
        input_path = Path(
            self._get_script_value("main", "logging_path"), self._get_script_value("main", "logging_name")
        )
        if input_path.exists():
            output_path = Path(
                self._get_workflow_value("main", "output_path"),
                f"{self._get_workflow_value('main', 'output_file_name')}{input_path.suffix}"
            )
            try:
                move(input_path, output_path)
                self.logger.info(
                    f"Logging file '{input_path.name}' moved from '{input_path.parent}' to '{output_path.parent}', "
                    f"final name: '{output_path.name}'"
                )
            except OSError as e:
                raise RuntimeError(
                    f"Error moving resulting file from '{input_path}' to '{output_path}'"
                ) from e
        else:
            self.logger.warning("VueScan logging file not found")

    def __call__(self, workflow_path: str, templates: dict[str, str]) -> None:
        """
        Execute the complete VueScan workflow.

        Args:
            workflow_path (str): Path to the workflow configuration directory.
            templates (dict[str, str]): Dictionary of initial template values.
        """
        self._templates = templates if templates else {}
        self._add_system_templates()
        self._workflow_path = Path(workflow_path).resolve()
        self.logger.info("Starting the workflow")
        self._read_settings()
        self._overwrite_vuescan_settings_file()
        self._run_vuescan()
        self._move_output_file()
        self._move_logging_file()
        self.logger.info("Workflow completed successfully")
