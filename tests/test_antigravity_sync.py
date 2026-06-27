import json
import tempfile
import unittest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]

def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class AntigravitySyncTests(unittest.TestCase):
    def test_sync_tasks_merges_checkbox_states(self):
        sync = load_module("antigravity_sync", "scripts/antigravity_sync.py")
        
        host_content = """# Tasks: Test Issue
- [ ] Task A
- [/] Task B
- [x] Task C
"""
        git_content = """# Tasks: Test Issue
Issue: 007-test

## Ready
- [x] PM: refine criteria [files: criteria.md]
- [ ] Task A
- [ ] Task B [files: b.py]
- [ ] Task C [files: c.py]
"""
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            host_path = tmp_root / "task.md"
            git_path = tmp_root / "tasks.md"
            
            host_path.write_text(host_content, encoding="utf-8")
            git_path.write_text(git_content, encoding="utf-8")
            
            # Sync host -> git
            sync.sync_tasks_bidirectional(host_path, git_path)
            
            updated_host = host_path.read_text(encoding="utf-8")
            updated_git = git_path.read_text(encoding="utf-8")
            
            # Verify B is [/] and C is [x] in both
            self.assertIn("- [/] Task B", updated_host)
            self.assertIn("- [/] Task B [files: b.py]", updated_git)
            
            self.assertIn("- [x] Task C", updated_host)
            self.assertIn("- [x] Task C [files: c.py]", updated_git)

    def test_detect_drift_flags_divergences(self):
        sync = load_module("antigravity_sync", "scripts/antigravity_sync.py")
        
        host_content = "- [x] Task A\n- [/] Task B\n"
        git_content = "- [ ] Task A\n- [x] Task B\n"
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            host_path = tmp_root / "task.md"
            git_path = tmp_root / "tasks.md"
            
            host_path.write_text(host_content, encoding="utf-8")
            git_path.write_text(git_content, encoding="utf-8")
            
            has_drift = sync.detect_task_drift(host_path, git_path)
            self.assertTrue(has_drift)

if __name__ == "__main__":
    unittest.main()
