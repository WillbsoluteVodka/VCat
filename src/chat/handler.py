"""
Chat handler for VCat dialog feature.
Manages chat history and message processing.
"""

from dataclasses import dataclass
from typing import List
from .commands import get_response


@dataclass
class ChatMessage:
    """Represents a single chat message."""
    text: str
    is_user: bool  # True if from user, False if from cat
    
    
class ChatHandler:
    """
    Handles chat messages and generates responses.
    Maintains chat history for the current session.
    """
    
    def __init__(self):
        self.history: List[ChatMessage] = []
        
    def send_message(self, user_input: str) -> str:
        """
        Process user input and generate a response.
        Returns the cat's response.
        """
        # Add user message to history
        user_message = ChatMessage(text=user_input, is_user=True)
        self.history.append(user_message)
        
        # Generate response
        response = get_response(user_input)
        
        # Add cat's response to history
        cat_message = ChatMessage(text=response, is_user=False)
        self.history.append(cat_message)
        
        return response
    
    def get_history(self) -> List[ChatMessage]:
        """Return the full chat history."""
        return self.history
    
    def clear_history(self):
        """Clear all chat history."""
        self.history = []
