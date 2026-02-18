from configparser import ConfigParser, ExtendedInterpolation
from shutil import SameFileError, copy2
from os.path import getmtime
from getpass import getuser
from subprocess import run
from pathlib import Path
from re import finditer
from os import makedirs
import datetime

from common.logger import Logger
from scan_batcher.workflows import register_workflow
from scan_batcher.workflow import MetadataWorkflow
from scan_batcher.constants import EXIF_DATETIME_FORMAT, EXIF_DATETIME_FORMAT_MS


@register_workflow("vuescan")
class VuescanWorkflow(MetadataWorkflow):
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

    def __init__(self, logger: Logger) -> None:
        """Initialize the VueScan workflow.
        
        Args:
            logger: Logger instance for this workflow.
        """
        super().__init__(logger)
        self._scan_datetime: datetime.datetime | None = None
        self._output_file_path: Path | None = None

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
            self._logger.info(f"Loading settings from '{str(path)}'")
            parser = ConfigParser(interpolation=ExtendedInterpolation())
            parser.read(path)
            self._logger.info("Settings loaded")
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
        self._logger.info(f"Workflow description: {self._get_workflow_value('main', 'description')}")

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
        self._logger.info(f"VueScan settings file '{path}' overwritten")

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
            self._logger.info(f"Launching VueScan from '{program_path}'")
            run([program_path], cwd=self._get_script_value("main", "program_path"), shell=False)
            self._logger.info("VueScan is closed")
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
                self._logger.warning(f"Error converting template '{string[1:-1]}' to value")
                continue
            result = result.replace(template, value)
        return result

    def _add_output_file_templates(self, path: Path) -> None:
        """
        Extract EXIF data from scanned file and add datetime templates.
        
        Also stores the datetime in self._scan_datetime for use by other methods.

        Args:
            path (Path): Path to the scanned file.
        """
        moment = None
        if path.suffix.lower() in self._EXIF_SUPPORTED_EXTENSIONS:
            try:
                tags = self._exifer.read(path, self._EXIF_DATE_TAGS)
                
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
                self._logger.warning(f"Unable to extract EXIF from file '{path.name}': {e}")

        if moment is None:
            moment = datetime.datetime.fromtimestamp(getmtime(path))

        # Ensure timezone is set (VueScan writes naive datetimes without TZ)
        if moment.tzinfo is None:
            local_offset = datetime.datetime.now(datetime.timezone.utc).astimezone().utcoffset()
            if local_offset is not None:
                moment = moment.replace(tzinfo=datetime.timezone(local_offset))

        # Store for use by _write_xmp_history
        self._scan_datetime = moment

        if moment:
            for key in self._EXIF_TEMPLATE_NAMES:
                self._templates[key] = getattr(moment, key.replace("digitization_", ""), "")

    @staticmethod
    def _parse_exif_datetime(value: str) -> datetime.datetime:
        """Parse EXIF datetime string to datetime object.
        
        Supports both standard EXIF format (YYYY:MM:DD HH:MM:SS)
        and format with fractional seconds (YYYY:MM:DD HH:MM:SS.fff).
        
        Args:
            value: EXIF datetime string.
            
        Returns:
            Parsed datetime object.
            
        Raises:
            ValueError: If the value cannot be parsed.
        """
        for fmt in (EXIF_DATETIME_FORMAT_MS, EXIF_DATETIME_FORMAT):
            try:
                return datetime.datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"Invalid EXIF datetime format: {value}")

    def _prepare_output_file(self) -> Path:
        """
        Locate the VueScan output file and extract EXIF templates from it.
        
        Finds the scanned file in VueScan's output directory, reads its EXIF
        data to populate datetime templates, and stores scan_datetime.
        
        Returns:
            Path to the VueScan output file (in its original location).
        
        Raises:
            FileNotFoundError: If output file not found after scanning.
        """
        input_path = Path(
            self._get_workflow_value("vuescan", "output_path"),
            f"{self._get_workflow_value('vuescan', 'output_file_name')}.{self._get_workflow_value('vuescan', 'output_extension_name')}"
        )
        if not input_path.exists():
            raise FileNotFoundError(f"Output file '{input_path}' not found after scanning")
        
        self._add_output_file_templates(input_path)
        return input_path

    def _write_xmp_history_for_scan(self, file_path: Path) -> None:
        """
        Write XMP history to the scanned file before it is moved.
        
        Args:
            file_path: Path to the scanned file (in its original location).
        """
        if self._scan_datetime is None:
            self._logger.warning("Cannot write XMP history: scan datetime not set")
            return
        
        self._write_xmp_history(file_path, self._scan_datetime)

    def _move_files(self, scan_file: Path) -> None:
        """
        Atomically move scanned file and its log to the final destination.

        Strategy (same as FileOrganizer):
        1. Copy scan file to ``<dest>.tmp``
        2. Copy log file (if exists) to destination
        3. Rename ``<dest>.tmp`` → ``<dest>`` (atomic on same volume)
        4. Delete originals

        If any step fails the partial copies are cleaned up and
        both originals are left untouched.

        Args:
            scan_file: Path to the scanned image (with XMP already written).
        """
        output_dir = self._get_workflow_value("main", "output_path")
        output_name = self._get_workflow_value("main", "output_file_name")

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        dest_scan = Path(output_dir, f"{output_name}{scan_file.suffix}")
        temp_scan = dest_scan.with_suffix(dest_scan.suffix + ".tmp")

        # Locate log file (optional)
        log_input = Path(
            self._get_script_value("main", "logging_path"),
            self._get_script_value("main", "logging_name"),
        )
        log_exists = log_input.exists()
        dest_log = Path(output_dir, f"{output_name}{log_input.suffix}") if log_exists else None

        try:
            # 1. Copy scan file to temp
            copy2(str(scan_file), str(temp_scan))
            self._logger.info(
                f"Scanned file '{scan_file.name}' copied to temp '{temp_scan.name}'"
            )

            # 2. Copy log file (if exists)
            if log_exists and dest_log is not None:
                copy2(str(log_input), str(dest_log))
                self._logger.info(
                    f"Logging file '{log_input.name}' copied to '{dest_log.name}'"
                )

            # 3. Atomic rename temp → final
            temp_scan.rename(dest_scan)
            self._output_file_path = dest_scan
            self._logger.info(
                f"Scanned file '{scan_file.name}' moved from '{scan_file.parent}' "
                f"to '{dest_scan.parent}', final name: '{dest_scan.name}'"
            )

            # 4. Delete originals
            scan_file.unlink()
            self._logger.info(f"Deleted source: {scan_file}")

            if log_exists:
                try:
                    log_input.unlink()
                    self._logger.info(f"Deleted source log: {log_input}")
                except OSError as e:
                    self._logger.warning(f"Failed to delete source log '{log_input}': {e}")

        except Exception as e:
            # Rollback: remove any partial copies
            self._logger.error(f"Failed to move files: {e}")
            for leftover in (temp_scan, dest_log):
                if leftover and leftover.exists():
                    try:
                        leftover.unlink()
                        self._logger.info(f"Cleaned up partial copy: {leftover}")
                    except OSError:
                        pass
            raise RuntimeError(
                f"Error moving scan files to '{output_dir}'"
            ) from e

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
        self._logger.info("Starting the workflow")
        self._read_settings()
        self._overwrite_vuescan_settings_file()
        self._run_vuescan()
        output_file = self._prepare_output_file()
        self._write_xmp_history_for_scan(output_file)
        self._move_files(output_file)
        self._logger.info("Workflow completed successfully")
