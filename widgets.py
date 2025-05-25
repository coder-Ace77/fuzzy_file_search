# textual_file_search/widgets.py

from textual.widgets import Input, ListView, ListItem, Label
from pathlib import Path
from typing import List, Optional
from textual.message import Message

class SearchInput(Input):
    """
    A custom Input widget.
    """
    pass # No custom methods needed in this specific widget for now

class SearchResultsList(ListView):
    """
    A ListView widget to display search results.
    Emits ResultSelected message when an item is chosen.
    """
    class ResultSelected(Message):
        """
        A message sent when a search result is selected (e.g., by pressing Enter).
        """
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    def __init__(self, id: Optional[str] = None) -> None:
        super().__init__(id=id)
        self._current_paths: List[Path] = []
        self.home_dir = Path.home() # Cache home directory for efficiency

    def update_results(self, paths: List[Path]) -> None:
        """
        Updates the list with new search results.
        """
        # Clear existing items
        for child in list(self.children):
            child.remove()
        
        self._current_paths = paths
        
        # Add new items, displaying paths relative to home directory
        for path in paths:
            display_str = str(path)
            try:
                # If the path is relative to home_dir, display it as such.
                # Prepend '~/' to indicate it's within the home directory.
                display_str = f"~/{path.relative_to(self.home_dir)}"
            except ValueError:
                # If the path is not within the home directory (e.g., /usr/bin/python),
                # display its full absolute path.
                pass 
            self.append(ListItem(Label(display_str)))
            
        # Select the first item if there are results, otherwise clear selection
        if self._current_paths:
            self.index = 0
        else:
            self.index = None # No item selected

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Handles selection in the list (triggered by ListView's internal logic).
        Posts a custom ResultSelected message.
        """
        if self.index is not None and 0 <= self.index < len(self._current_paths):
            selected_path = self._current_paths[self.index]
            self.post_message(self.ResultSelected(selected_path))