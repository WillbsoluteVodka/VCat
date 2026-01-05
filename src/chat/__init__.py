# Chat module for VCat dialog feature
from .handler import ChatHandler
from .commands import COMMANDS, get_response

__all__ = ['ChatHandler', 'COMMANDS', 'get_response']
