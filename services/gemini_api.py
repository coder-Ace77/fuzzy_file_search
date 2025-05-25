# textual_file_search/services/gemini_api.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class GeminiAPI:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in a .env file.")
        
        genai.configure(api_key=api_key)
        
        # Initialize the model with chat capabilities
        # Using a model that supports multi-turn conversations
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.chat_session = self.model.start_chat(history=[])

    async def send_message(self, message: str) -> str:
        """Sends a message to the Gemini API and returns the response."""
        try:
            response = await self.chat_session.send_message_async(message)
            return response.text
        except Exception as e:
            return f"Error: Could not get response from Gemini API. {e}"

    def reset_chat(self):
        """Resets the current chat session history."""
        self.chat_session = self.model.start_chat(history=[])

# Example usage (for testing, not part of the app flow directly)
async def main():
    gemini = GeminiAPI()
    print("Chatting with Gemini. Type 'quit' to exit.")
    while True:
        user_message = input("You: ")
        if user_message.lower() == 'quit':
            break
        response = await gemini.send_message(user_message)
        print(f"Gemini: {response}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())