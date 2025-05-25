# textual_file_search/apps/fuzzy_file_search.py

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Input
from textual.reactive import reactive
from textual import log
from textual.events import Key

# Relative imports from the textual_file_search package
from widgets import SearchInput, SearchResultsList
from search import get_home_directory_files, fuzzy_search
from utils import open_file_or_directory

from pathlib import Path
from typing import List

class FileSearchApp(App):
    """
    A Textual app for fuzzy searching files in the home directory.
    """
    CSS_PATH = "../tcss/app.tcss" # Link to our CSS file (relative to this file)
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+s", "focus_search", "Focus Search"), # Custom binding to quickly focus search
    ]

    # Reactive state to store all home directory paths (loaded once)
    all_home_paths: reactive[List[Path]] = reactive(list)
    # Reactive state for the currently displayed search results
    current_search_results: reactive[List[Path]] = reactive(list)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app's layout."""
        yield Header()
        with Container(): # A container to hold the input and results list
            yield SearchInput(placeholder="Type to search...", id="search-input")
            yield SearchResultsList(id="results-list")
        yield Footer()

    def on_mount(self) -> None:
        """Called after the app is mounted (initialized)."""
        # Load files in a background worker to keep the UI responsive
        self.run_worker(self._load_files_worker(), name="file_loader")
        # Set initial focus to the search input
        self.query_one(SearchInput).focus()

    async def _load_files_worker(self) -> None:
        """Worker function to load all files from the home directory."""
        self.log("Starting to load home directory files...")
        search_input = self.query_one(SearchInput)
        search_input.placeholder = "Loading files... Please wait."
        
        try:
            self.all_home_paths = get_home_directory_files()
            self.log(f"Loaded {len(self.all_home_paths)} files and directories.")
        finally:
            search_input.placeholder = "Type to search..."
            search_input.refresh() # Update the placeholder text in the UI

    async def watch_current_search_results(self, results: List[Path]) -> None:
        """
        Called automatically by Textual when `current_search_results` reactive state changes.
        Updates the `SearchResultsList` widget.
        """
        results_list = self.query_one(SearchResultsList)
        results_list.update_results(results)

    async def on_input_changed(self, event: Input.Changed) -> None:
        """
        Handles the standard `Input.Changed` message.
        Performs the fuzzy search and updates the `current_search_results`.
        """
        query = event.value 
        self.current_search_results = fuzzy_search(query, self.all_home_paths, limit=10)

    async def on_key(self, event: Key) -> None:
        """
        Global key event handler for navigation between input and list,
        and for opening files.
        """
        search_input = self.query_one(SearchInput)
        results_list = self.query_one(SearchResultsList)

        if event.key == "down":
            if self.focused == search_input:
                if self.current_search_results:
                    results_list.focus()
                    event.prevent_default()
            elif self.focused == results_list:
                if results_list.index is not None and results_list.index < len(self.current_search_results) - 1:
                    results_list.action_cursor_down() 
                    event.prevent_default()

        elif event.key == "up":
            if self.focused == results_list:
                if results_list.index == 0:
                    search_input.focus()
                    results_list.index = None
                    event.prevent_default()
                elif results_list.index is not None and results_list.index > 0:
                    results_list.action_cursor_up()
                    event.prevent_default()

        elif event.key == "enter":
            if self.focused == search_input:
                if self.current_search_results:
                    selected_path = self.current_search_results[0]
                    open_file_or_directory(selected_path)
                    search_input.value = ""
                    self.current_search_results = []
                    event.prevent_default()
            elif self.focused == results_list:
                if results_list.index is not None and 0 <= results_list.index < len(self.current_search_results):
                    selected_path = self.current_search_results[results_list.index]
                    open_file_or_directory(selected_path)
                    search_input.value = ""
                    self.current_search_results = []
                    search_input.focus()
                    event.prevent_default()

    async def on_search_results_list_result_selected(self, event: SearchResultsList.ResultSelected) -> None:
        """
        Handles the custom `ResultSelected` message from `SearchResultsList`.
        """
        open_file_or_directory(event.path)
        self.query_one(SearchInput).value = ""
        self.current_search_results = []
        self.query_one(SearchInput).focus()

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_focus_search(self) -> None:
        """Action to focus the search input."""
        self.query_one(SearchInput).focus()