"""
File-based persistence system for agent registry.

This module provides thread-safe, atomic file operations for storing and
retrieving agent registry data with backup and recovery capabilities.
"""

import json
import logging
import os
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FileStoreError(Exception):
    """Base exception for FileStore operations."""
    pass


class FileStore:
    """
    Thread-safe file storage with atomic writes and backup/restore capabilities.

    Features:
    - Atomic writes (write to temp file, then rename)
    - Automatic backups before modifications
    - Thread-safe operations
    - JSON schema validation
    - Corrupted file recovery
    """

    # JSON schema for registry data
    SCHEMA = {
        "version": str,
        "last_updated": str,
        "agents": dict
    }

    def __init__(self, file_path: str = "agent_registry_service/data/registry_config.json"):
        """
        Initialize FileStore.

        Args:
            file_path: Path to the registry JSON file
        """
        self.file_path = Path(file_path)
        self.backup_path = Path(f"{file_path}.backup")
        self.temp_path = Path(f"{file_path}.tmp")
        self._lock = threading.Lock()

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"FileStore initialized with path: {self.file_path}")

    def save(self, registry_data: Dict) -> bool:
        """
        Save registry data to file with atomic writes.

        Process:
        1. Create backup of existing file
        2. Write to temporary file
        3. Validate written data
        4. Atomically rename temp file to target file

        Args:
            registry_data: Dictionary containing registry data

        Returns:
            True if save successful, False otherwise

        Raises:
            FileStoreError: If save operation fails
        """
        with self._lock:
            try:
                # Add metadata if not present
                if "version" not in registry_data:
                    registry_data["version"] = "1.0.0"
                if "last_updated" not in registry_data:
                    registry_data["last_updated"] = datetime.now(timezone.utc).isoformat()

                # Validate data structure
                self._validate_schema(registry_data)

                # Create backup before modification
                if self.file_path.exists():
                    if not self.backup():
                        logger.warning("Backup creation failed, proceeding with save anyway")

                # Write to temporary file (atomic operation prep)
                with open(self.temp_path, 'w', encoding='utf-8') as f:
                    json.dump(registry_data, f, indent=2, ensure_ascii=False)

                # Verify temp file is valid JSON
                with open(self.temp_path, 'r', encoding='utf-8') as f:
                    json.load(f)

                # Atomic rename (this is atomic on POSIX systems)
                shutil.move(str(self.temp_path), str(self.file_path))

                logger.info(f"Registry data saved successfully to {self.file_path}")
                return True

            except Exception as e:
                logger.error(f"Failed to save registry data: {e}", exc_info=True)
                # Clean up temp file if it exists
                if self.temp_path.exists():
                    self.temp_path.unlink()
                raise FileStoreError(f"Save operation failed: {e}")

    def load(self) -> Dict:
        """
        Load registry data from file with validation.

        If file is corrupted, attempts to restore from backup.
        If no valid file exists, returns empty registry structure.

        Returns:
            Dictionary containing registry data

        Raises:
            FileStoreError: If load operation fails critically
        """
        with self._lock:
            try:
                # Try to load main file
                if self.file_path.exists():
                    data = self._load_and_validate(self.file_path)
                    if data:
                        logger.info(f"Registry data loaded successfully from {self.file_path}")
                        return data
                    else:
                        logger.warning(f"Main file corrupted, attempting backup restore")

                # Try to restore from backup
                if self.backup_path.exists():
                    logger.info("Attempting to restore from backup")
                    if self.restore_from_backup():
                        data = self._load_and_validate(self.file_path)
                        if data:
                            logger.info("Successfully restored from backup")
                            return data

                # No valid file found, return empty registry
                logger.info("No valid registry file found, returning empty registry")
                return self._get_empty_registry()

            except Exception as e:
                logger.error(f"Failed to load registry data: {e}", exc_info=True)
                raise FileStoreError(f"Load operation failed: {e}")

    def backup(self) -> bool:
        """
        Create backup of current registry file.

        Returns:
            True if backup successful, False otherwise
        """
        try:
            if not self.file_path.exists():
                logger.debug("No file to backup")
                return False

            shutil.copy2(str(self.file_path), str(self.backup_path))
            logger.info(f"Backup created at {self.backup_path}")
            return True

        except Exception as e:
            logger.error(f"Backup creation failed: {e}", exc_info=True)
            return False

    def restore_from_backup(self) -> bool:
        """
        Restore registry from backup file.

        Returns:
            True if restore successful, False otherwise
        """
        try:
            if not self.backup_path.exists():
                logger.error("No backup file found")
                return False

            # Validate backup before restoring
            data = self._load_and_validate(self.backup_path)
            if not data:
                logger.error("Backup file is corrupted")
                return False

            shutil.copy2(str(self.backup_path), str(self.file_path))
            logger.info(f"Registry restored from backup")
            return True

        except Exception as e:
            logger.error(f"Restore from backup failed: {e}", exc_info=True)
            return False

    def _load_and_validate(self, file_path: Path) -> Optional[Dict]:
        """
        Load and validate JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary if valid, None if corrupted
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate schema
            self._validate_schema(data)
            return data

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"File validation failed for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading {file_path}: {e}")
            return None

    def _validate_schema(self, data: Dict) -> None:
        """
        Validate data against expected schema.

        Args:
            data: Dictionary to validate

        Raises:
            ValueError: If schema validation fails
        """
        for key, expected_type in self.SCHEMA.items():
            if key not in data:
                raise ValueError(f"Missing required field: {key}")
            if not isinstance(data[key], expected_type):
                raise ValueError(
                    f"Invalid type for {key}: expected {expected_type.__name__}, "
                    f"got {type(data[key]).__name__}"
                )

    def _get_empty_registry(self) -> Dict:
        """
        Get empty registry structure.

        Returns:
            Dictionary with empty registry structure
        """
        return {
            "version": "1.0.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "agents": {}
        }
