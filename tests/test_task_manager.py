import os
import sys
import pytest
import tempfile
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.task.task_manager import TaskManager, ConvertTask


class TestConvertTask:
    def test_task_creation(self):
        task = ConvertTask("test.pdf", "test.epub")
        assert task.status == "pending"
        assert task.progress == 0
        assert task.error is None
        assert task.pdf_path == "test.pdf"
        assert task.output_path == "test.epub"

    def test_task_default_values(self):
        task = ConvertTask("input.pdf", "")
        assert task.status == "pending"
        assert task.output_path == ""
        assert task.chapters == []
        assert task.image_count == 0


class TestTaskManager:
    @pytest.fixture
    def manager(self):
        mgr = TaskManager(max_workers=2)
        return mgr

    def test_add_task(self, manager):
        task = manager.add_task("dummy.pdf", "dummy.epub")
        assert task in manager.tasks
        assert task.status == "pending"

    def test_add_duplicate_task(self, manager):
        manager.add_task("dummy.pdf", "dummy.epub")
        manager.add_task("dummy.pdf", "dummy.epub")
        assert len(manager.tasks) == 2

    def test_clear_tasks(self, manager):
        manager.add_task("dummy.pdf", "dummy.epub")
        manager.clear_tasks()
        assert len(manager.tasks) == 0

    def test_get_summary(self, manager):
        manager.add_task("a.pdf", "a.epub")
        manager.add_task("b.pdf", "b.epub")
        summary = manager.get_summary()
        assert summary["total"] == 2
        assert summary["pending"] == 2

    def test_cancel_all(self, manager):
        manager.add_task("dummy.pdf", "dummy.epub")
        manager.tasks[0].status = "running"
        manager.cancel_all()
        assert manager.tasks[0].status == "cancelled"

    def test_add_tasks(self, manager):
        pdf_paths = ["a.pdf", "b.pdf"]
        tasks = manager.add_tasks(pdf_paths, "/tmp/output")
        assert len(tasks) == 2
        assert all(t.status == "pending" for t in tasks)

    def test_execute_callback(self, manager):
        manager.add_task("nonexistent.pdf", "out.epub")
        callback_data = []

        def cb(summary):
            callback_data.append(summary)

        manager.execute(callback=cb)
        manager.wait_completion()
        assert len(callback_data) > 0