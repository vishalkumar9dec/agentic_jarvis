"""
Comprehensive unit tests for FileStore.

Tests cover:
- Save and load operations
- Atomic writes
- Backup and restore
- Corrupted file handling
- Concurrent access
- Schema validation
"""

import json
import os
import pytest
import tempfile
import threading
import time
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent_registry_service.registry.file_store import FileStore, FileStoreError


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_store(temp_dir):
    """Create FileStore instance with temporary file path."""
    file_path = os.path.join(temp_dir, "test_registry.json")
    return FileStore(file_path)


@pytest.fixture
def sample_registry_data():
    """Sample registry data for testing."""
    return {
        "version": "1.0.0",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "agents": {
            "test_agent": {
                "name": "test_agent",
                "description": "Test agent",
                "enabled": True
            }
        }
    }


class TestFileStoreSaveAndLoad:
    """Test save and load operations."""

    def test_save_and_load_basic(self, file_store, sample_registry_data):
        """Test basic save and load functionality."""
        # Save data
        result = file_store.save(sample_registry_data)
        assert result is True

        # Load data
        loaded_data = file_store.load()
        assert loaded_data["version"] == sample_registry_data["version"]
        assert loaded_data["agents"] == sample_registry_data["agents"]

    def test_save_creates_file(self, file_store, sample_registry_data):
        """Test that save creates the file."""
        assert not file_store.file_path.exists()

        file_store.save(sample_registry_data)
        assert file_store.file_path.exists()

    def test_save_adds_metadata(self, file_store):
        """Test that save adds version and last_updated if missing."""
        data = {"agents": {}}
        file_store.save(data)

        loaded_data = file_store.load()
        assert "version" in loaded_data
        assert "last_updated" in loaded_data
        assert loaded_data["version"] == "1.0.0"

    def test_load_empty_file_returns_empty_registry(self, file_store):
        """Test that loading non-existent file returns empty registry."""
        loaded_data = file_store.load()
        assert loaded_data["version"] == "1.0.0"
        assert loaded_data["agents"] == {}
        assert "last_updated" in loaded_data

    def test_save_invalid_schema_raises_error(self, file_store):
        """Test that saving invalid schema raises error."""
        invalid_data = {"version": "1.0.0"}  # Missing required fields

        with pytest.raises(FileStoreError):
            file_store.save(invalid_data)


class TestAtomicWrites:
    """Test atomic write operations."""

    def test_atomic_write_no_partial_writes(self, file_store, sample_registry_data):
        """Test that failed writes don't leave partial files."""
        # First save succeeds
        file_store.save(sample_registry_data)

        # Simulate write failure by making invalid data
        invalid_data = {"version": 123, "last_updated": "test", "agents": {}}  # Invalid type

        with pytest.raises(FileStoreError):
            file_store.save(invalid_data)

        # Original file should still be intact
        loaded_data = file_store.load()
        assert loaded_data["agents"] == sample_registry_data["agents"]

    def test_temp_file_cleaned_up_on_error(self, file_store):
        """Test that temporary file is cleaned up on error."""
        invalid_data = {"version": 123, "last_updated": "test", "agents": {}}

        try:
            file_store.save(invalid_data)
        except FileStoreError:
            pass

        # Temp file should not exist
        assert not file_store.temp_path.exists()

    def test_concurrent_saves_are_serialized(self, file_store, sample_registry_data):
        """Test that concurrent saves are properly serialized."""
        results = []
        errors = []

        def save_data(agent_id):
            try:
                data = sample_registry_data.copy()
                data["agents"] = {f"agent_{agent_id}": {"id": agent_id}}
                result = file_store.save(data)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=save_data, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All saves should succeed
        assert len(errors) == 0
        assert len(results) == 10
        assert all(r is True for r in results)

        # Final file should be valid
        loaded_data = file_store.load()
        assert "agents" in loaded_data


class TestBackupAndRestore:
    """Test backup and restore functionality."""

    def test_backup_creates_backup_file(self, file_store, sample_registry_data):
        """Test that backup creates backup file."""
        file_store.save(sample_registry_data)

        result = file_store.backup()
        assert result is True
        assert file_store.backup_path.exists()

    def test_backup_without_file_returns_false(self, file_store):
        """Test that backup without existing file returns False."""
        result = file_store.backup()
        assert result is False

    def test_save_creates_backup_automatically(self, file_store, sample_registry_data):
        """Test that save creates backup of existing file."""
        # First save
        file_store.save(sample_registry_data)
        assert not file_store.backup_path.exists()

        # Second save should create backup
        modified_data = sample_registry_data.copy()
        modified_data["agents"]["new_agent"] = {"id": "new"}
        file_store.save(modified_data)

        assert file_store.backup_path.exists()

    def test_restore_from_backup(self, file_store, sample_registry_data):
        """Test restoring from backup."""
        # Save original data
        file_store.save(sample_registry_data)

        # Modify and save (creates backup)
        modified_data = sample_registry_data.copy()
        modified_data["agents"]["modified_agent"] = {"id": "modified"}
        file_store.save(modified_data)

        # Restore from backup
        result = file_store.restore_from_backup()
        assert result is True

        # Loaded data should be original
        loaded_data = file_store.load()
        assert "modified_agent" not in loaded_data["agents"]
        assert "test_agent" in loaded_data["agents"]

    def test_restore_without_backup_returns_false(self, file_store):
        """Test that restore without backup returns False."""
        result = file_store.restore_from_backup()
        assert result is False


class TestCorruptedFileHandling:
    """Test handling of corrupted files."""

    def test_load_corrupted_file_tries_backup(self, file_store, sample_registry_data):
        """Test that loading corrupted file attempts backup restore."""
        # Save valid data (creates backup on second save)
        file_store.save(sample_registry_data)
        file_store.save(sample_registry_data)

        # Corrupt main file
        with open(file_store.file_path, 'w') as f:
            f.write("invalid json {{{")

        # Load should restore from backup
        loaded_data = file_store.load()
        assert loaded_data["agents"] == sample_registry_data["agents"]

    def test_load_corrupted_file_without_backup_returns_empty(self, file_store):
        """Test that corrupted file without backup returns empty registry."""
        # Create corrupted file
        file_store.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_store.file_path, 'w') as f:
            f.write("invalid json {{{")

        # Load should return empty registry
        loaded_data = file_store.load()
        assert loaded_data["agents"] == {}
        assert loaded_data["version"] == "1.0.0"

    def test_corrupted_backup_handled_gracefully(self, file_store, sample_registry_data):
        """Test that corrupted backup is handled gracefully."""
        # Save data
        file_store.save(sample_registry_data)

        # Create corrupted backup
        with open(file_store.backup_path, 'w') as f:
            f.write("invalid json")

        # Corrupt main file
        with open(file_store.file_path, 'w') as f:
            f.write("also invalid")

        # Should return empty registry
        loaded_data = file_store.load()
        assert loaded_data["agents"] == {}


class TestConcurrentAccess:
    """Test concurrent access patterns."""

    def test_concurrent_reads(self, file_store, sample_registry_data):
        """Test that concurrent reads work correctly."""
        file_store.save(sample_registry_data)

        results = []
        errors = []

        def read_data():
            try:
                data = file_store.load()
                results.append(data)
            except Exception as e:
                errors.append(e)

        # Create multiple reader threads
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=read_data)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All reads should succeed
        assert len(errors) == 0
        assert len(results) == 20
        assert all(r["agents"] == sample_registry_data["agents"] for r in results)

    def test_concurrent_read_write(self, file_store, sample_registry_data):
        """Test concurrent reads and writes."""
        file_store.save(sample_registry_data)

        errors = []

        def read_data():
            try:
                for _ in range(5):
                    file_store.load()
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def write_data(agent_id):
            try:
                for _ in range(5):
                    data = sample_registry_data.copy()
                    data["agents"][f"agent_{agent_id}"] = {"id": agent_id}
                    file_store.save(data)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Create reader and writer threads
        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=read_data))
            threads.append(threading.Thread(target=write_data, args=(i,)))

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # No errors should occur
        assert len(errors) == 0


class TestSchemaValidation:
    """Test JSON schema validation."""

    def test_missing_version_field_added(self, file_store):
        """Test that missing version field is added."""
        data = {"agents": {}}
        file_store.save(data)

        loaded_data = file_store.load()
        assert "version" in loaded_data

    def test_missing_last_updated_field_added(self, file_store):
        """Test that missing last_updated field is added."""
        data = {"agents": {}}
        file_store.save(data)

        loaded_data = file_store.load()
        assert "last_updated" in loaded_data

    def test_invalid_type_raises_error(self, file_store):
        """Test that invalid field types raise errors."""
        data = {"version": 123, "last_updated": "test", "agents": {}}  # version should be str

        with pytest.raises(FileStoreError):
            file_store.save(data)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
