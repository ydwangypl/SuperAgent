import unittest
import sys
from pathlib import Path
import tempfile
import os
import asyncio

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from context.incremental_updater import (
    IncrementalUpdater,
    IncrementalConfig,
    FileSnapshot
)

class TestIncrementalUpdater(unittest.IsolatedAsyncioTestCase):
    """IncrementalUpdater Tests"""

    async def test_snapshot_creation(self):
        """Test snapshot creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = IncrementalUpdater(
                project_root=Path(tmpdir),
                config=IncrementalConfig(enabled=True)
            )

            # Create test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, World!")

            # Take snapshot
            snapshot = await updater.take_snapshot("test.txt")

            # Verify results
            self.assertIsNotNone(snapshot, "Snapshot should not be None")
            self.assertEqual(snapshot.path, "test.txt", "Path should be correct")
            self.assertEqual(snapshot.size, len("Hello, World!"), "Size should be correct")
            self.assertIsNotNone(snapshot.hash, "Hash should not be None")

    async def test_change_detection(self):
        """Test change detection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = IncrementalUpdater(
                project_root=Path(tmpdir),
                config=IncrementalConfig(enabled=True, incremental_threshold=0.3)
            )

            # Create initial file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    print('Hello')\n")

            # Take initial snapshot
            await updater.take_snapshot("test.py")

            # Modify file
            test_file.write_text("def hello():\n    print('Hello, World!')\n    print('New line')\n")

            # Detect changes
            change = await updater.detect_changes("test.py", "test.py")

            # Verify results
            self.assertEqual(change.change_type, "modified", "Should be modified type")
            self.assertGreater(change.diff_ratio, 0, "Diff ratio should be greater than 0")

    async def test_incremental_update(self):
        """Test incremental update"""
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = IncrementalUpdater(
                project_root=Path(tmpdir),
                config=IncrementalConfig(
                    enabled=True,
                    incremental_threshold=0.5
                )
            )

            # 1. Create initial file
            test_file = Path(tmpdir) / "app.py"
            test_file.write_text("def main():\n    pass\n")
            
            # 2. Take initial snapshot
            await updater.take_snapshot("app.py")
            
            # 3. Modify file slightly
            test_file.write_text("def main():\n    print('starting...')\n    pass\n")
            
            # 4. Detect changes
            change = await updater.detect_changes("app.py", "app.py")
            
            # 5. Verify it's an incremental update
            # Since we have old snapshot, diff should be generated
            self.assertIsNotNone(change.diff)
            self.assertLess(change.diff_ratio, 0.5)

    async def test_project_changes(self):
        """Test project-wide change detection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            updater = IncrementalUpdater(
                project_root=project_dir,
                config=IncrementalConfig(enabled=True)
            )

            # 1. Create some files
            (project_dir / "a.py").write_text("content a")
            (project_dir / "b.py").write_text("content b")
            
            # 2. Take project snapshot
            initial_snapshots = await updater.take_project_snapshot()
            self.assertEqual(len(initial_snapshots), 2)
            
            # 3. Modify one file, delete one, add one
            (project_dir / "a.py").write_text("content a modified")
            (project_dir / "b.py").unlink()
            (project_dir / "c.py").write_text("content c")
            
            # 4. Detect project changes
            changes = await updater.detect_project_changes(before_snapshots=initial_snapshots)
            
            # 5. Verify changes
            change_types = {c.path: c.change_type for c in changes}
            self.assertEqual(change_types.get("a.py"), "modified")
            self.assertEqual(change_types.get("b.py"), "deleted")
            self.assertEqual(change_types.get("c.py"), "added")

if __name__ == "__main__":
    unittest.main()
