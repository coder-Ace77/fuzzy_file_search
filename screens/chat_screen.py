# textual_file_search/screens/chat_screen.py

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Static, Markdown
from textual.containers import VerticalScroll, Horizontal
from textual.reactive import reactive
from textual.message import Message

from services.gemini_api import GeminiAPI

from typing import List, Tuple

# Define a type for chat messages (sender, content)
ChatMessage = Tuple[str, str] # "user" or "ai", message_content

class ChatScreen(Screen):
    """A screen for interacting with the Gemini AI."""

    CSS_PATH = "../tcss/chat_screen.tcss" # Link to its own CSS

    # Reactive list to hold chat history (user message, AI response)
    chat_history: reactive[List[ChatMessage]] = reactive(list)
    
    def __init__(self, name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name=name, id=id, classes=classes)
        self.gemini_api = GeminiAPI() # Initialize Gemini API client
        self.scroll_container = VerticalScroll(id="chat-display")
        self.chat_input = Input(placeholder="Ask Gemini...", id="chat-input")

    def compose(self) -> ComposeResult:
        # yield Header()
        yield self.scroll_container # Scrollable area for chat messages
        with Horizontal(id="chat-controls"):
            yield self.chat_input
            yield Button("Send", id="send-button", variant="primary")
            yield Button("Reset", id="reset-button", variant="warning")
        # yield Footer()

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        self.chat_input.focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handles when the user submits input (presses Enter)."""
        user_message = event.value.strip()
        self.chat_input.value = "" # Clear input immediately

        if not user_message:
            return

        # Add user message to history
        self.chat_history.append(("user", user_message))
        self._add_message_to_display("user", user_message)
        self.scroll_container.scroll_end() # Scroll to bottom

        # Show a loading indicator
        self.chat_input.placeholder = "Gemini is thinking..."
        self.chat_input.disabled = True
        self.query_one("#send-button", Button).disabled = True
        self.query_one("#reset-button", Button).disabled = True # Also disable reset while thinking

        # Send message to Gemini API (in a worker to keep UI responsive)
        # Corrected: Pass the coroutine object, not the awaited result of the coroutine.
        # Then, await the worker object itself.
        try:
            worker = self.run_worker(self.gemini_api.send_message(user_message), exclusive=True)
            ai_response = await worker.wait() # Await the worker to get its result
        except Exception as e:
            ai_response = f"Error: Failed to get AI response: {e}"
            self.log(f"Worker error: {e}") # Log the error for debugging

        # Add AI response to history
        self.chat_history.append(("ai", ai_response))
        self._add_message_to_display("ai", ai_response)
        self.scroll_container.scroll_end() # Scroll to bottom again after AI response

        # Reset input state
        self.chat_input.placeholder = "Ask Gemini..."
        self.chat_input.disabled = False
        self.query_one("#send-button", Button).disabled = False
        self.query_one("#reset-button", Button).disabled = False # Re-enable reset
        self.chat_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button presses."""
        if event.button.id == "send-button":
            # Manually trigger input submission when send button is pressed
            self.post_message(Input.Submitted(self.chat_input, self.chat_input.value))
        elif event.button.id == "reset-button":
            self.action_reset_chat()

    def watch_chat_history(self, history: List[ChatMessage]) -> None:
        """Watcher method for chat_history reactive variable."""
        pass

    def _add_message_to_display(self, sender: str, content: str) -> None:
        """Helper to add a message to the chat display."""
        # Use Markdown widget for richer text display of AI responses
        message_widget = Markdown(content, classes=f"message {sender}-message")
        self.scroll_container.mount(message_widget)
        self.scroll_container.scroll_end() # Auto-scroll to latest message

    def action_reset_chat(self) -> None:
        """Action to reset the chat session."""
        self.gemini_api.reset_chat()
        self.chat_history.clear()
        # Remove all existing message widgets from the display
        for child in list(self.scroll_container.children):
            if isinstance(child, Markdown) and "message" in child.classes:
                child.remove()
        self.scroll_container.scroll_end()
        self.chat_input.focus()
        self.notify("Chat history reset.")