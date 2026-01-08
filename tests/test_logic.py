import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# -----------------------------------------------------------------------------

import pytest
import json
from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import QTreeWidget, QLineEdit, QLabel

# Import the classes we want to test
from data_history import DataHistory
from data_parser import DataParser
from tree_core import TreeCore
from task_tree import TodoItem

# --- MOCKS ---
# We mock DataManager and MainWindow to avoid launching the entire application during tests.

class MockDataManager:
    """Mock for the database manager."""
    def __init__(self):
        self.current_note_id = "test_note_id"
        self.all_notes = {
            "test_note_id": {
                "title": "Test Note",
                "tasks": [],
                "start_time_str": None,
                "finish_time_str": None
            }
        }
        self.start_time = None
        self.finish_time = None
        self.save_called = False

    def save_to_disk(self, skip_history=False):
        self.save_called = True

class MockMainWindow:
    """Mock for the main window (required by TreeCore)."""
    def __init__(self):
        self.data = MockDataManager()
        self.tree = QTreeWidget()
        self.inp = QLineEdit() # Input field
        self.title = QLabel()  # Title label
        # Mocking progress bar with a dummy object
        self.progress = type('obj', (object,), {'setValue': lambda s, v: None})

# --- HISTORY TESTS (Undo/Redo) ---

def test_history_undo_redo():
    """Verify that Undo (Ctrl+Z) and Redo (Ctrl+Y) work correctly."""
    dm = MockDataManager()
    history = DataHistory(dm)

    # 1. Initial state (empty list)
    initial_tasks = []
    
    # 2. Add tasks (simulating user actions)
    state_1 = [{"text": "Task 1", "checked": False}]
    history.add_to_history(state_1)
    
    state_2 = [{"text": "Task 1", "checked": False}, {"text": "Task 2", "checked": True}]
    history.add_to_history(state_2)

    # We are now in state_2. Verify Undo (should return to state_1)
    assert history.undo() is True
    assert dm.all_notes[dm.current_note_id]["tasks"] == state_1
    
    # Verify Redo (should return to state_2)
    assert history.redo() is True
    assert dm.all_notes[dm.current_note_id]["tasks"] == state_2

def test_history_limit():
    """Verify that the history does not grow strictly beyond 50 items."""
    dm = MockDataManager()
    history = DataHistory(dm)
    
    # Fill history with 60 entries
    for i in range(60):
        history.add_to_history([{"id": i}])
        
    assert len(history.history) <= 50
    # Verify that old records were removed and new ones remain
    assert history.history[-1] == [{"id": 59}]

# --- PARSER TESTS (Time and Titles) ---

def test_timings_parsing():
    """Verify that time strings are correctly parsed into QDateTime objects."""
    dm = MockDataManager()
    parser = DataParser(dm)
    
    # Inject a date string
    test_date_str = "24.12.2025 15:30:00"
    dm.all_notes[dm.current_note_id]["start_time_str"] = test_date_str
    
    parser.load_timings()
    
    assert dm.start_time is not None
    assert dm.start_time.toString("dd.MM.yyyy HH:mm:ss") == test_date_str

# --- TREE LOGIC TESTS (TreeCore) ---

def test_add_task(qtbot):
    """
    Verify adding a task to the tree.
    qtbot is a pytest-qt fixture required for widget interaction.
    """
    mw = MockMainWindow()
    
    # Save callback mock
    save_flag = {"saved": False}
    def mock_save(): save_flag["saved"] = True
    
    core = TreeCore(mw, mock_save)
    
    # Add a task
    core.add_task("New Task")
    
    # Assertions
    assert mw.tree.topLevelItemCount() == 1
    item = mw.tree.topLevelItem(0)
    assert item.text(0) == "New Task"
    assert item.checkState(0) == Qt.CheckState.Unchecked
    # Verify save was called
    assert save_flag["saved"] is True

def test_task_indentation(qtbot):
    """Verify task nesting (indentation via Tab/Ctrl+Right)."""
    mw = MockMainWindow()
    core = TreeCore(mw, lambda: None)
    
    # Create two tasks
    item1 = TodoItem(mw.tree, "Parent")
    item2 = TodoItem(mw.tree, "Child Candidate")
    
    # Select the second task
    mw.tree.setCurrentItem(item2)
    
    # Indent -> item2 should become a child of item1
    core.indent()
    
    assert mw.tree.topLevelItemCount() == 1 # Only Parent remains at top level
    parent = mw.tree.topLevelItem(0)
    assert parent.childCount() == 1
    assert parent.child(0).text(0) == "Child Candidate"

def test_task_completion_logic(qtbot):
    """Verify logic: if parent is checked, children must be checked too."""
    mw = MockMainWindow()
    core = TreeCore(mw, lambda: None)
    
    # Create hierarchy: Parent -> Child
    parent = TodoItem(mw.tree, "Parent")
    child = TodoItem(parent, "Child")
    
    # Check the parent
    parent.setCheckState(0, Qt.CheckState.Checked)
    
    # Trigger logic
    core.on_item_changed(parent)
    
    # Verify child is also checked
    assert child.checkState(0) == Qt.CheckState.Checked