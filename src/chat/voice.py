"""
Voice recognition module for VCat using macOS NSSpeechRecognizer.
Provides voice wake-up functionality ONLY.

IMPORTANT: NSSpeechRecognizer only supports PREDEFINED COMMANDS.
This module is used ONLY for wake word detection ("Hey Cat", "Hey Kitty").
For actual speech-to-text, use macOS Dictation (triggered via keyboard shortcut).
"""

from AppKit import NSSpeechRecognizer
from Foundation import NSObject
from PyQt5.QtCore import QObject, pyqtSignal
import objc


class VoiceRecognizerDelegate(NSObject):
    """
    Objective-C delegate for NSSpeechRecognizer.
    Handles speech recognition callbacks.
    """
    
    def initWithCallback_(self, callback):
        self = objc.super(VoiceRecognizerDelegate, self).init()
        if self is None:
            return None
        self.callback = callback
        return self
    
    def speechRecognizer_didRecognizeCommand_(self, sender, command):
        """Called when a command is recognized."""
        print(f"[Voice] Recognized: {command}")
        if self.callback:
            self.callback(command)


class VoiceRecognizer(QObject):
    """
    Qt wrapper for macOS NSSpeechRecognizer.
    Used ONLY for wake word detection ("Hey Cat", "Hey Kitty", etc.)
    
    For actual voice input/transcription, use MacOSDictation class instead.
    """
    
    # Signal emitted when wake word is detected
    wake_word_detected = pyqtSignal()
    
    # Wake words ONLY - no command phrases
    WAKE_WORDS = [
        "Hey Cat",
        "Hey Kitty", 
        "Hello Cat",
        "Hi Cat",
        "Cat",
        "Kitty",
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recognizer = None
        self.delegate = None
        self.is_listening = False
        
    def start(self):
        """Start listening for wake words."""
        if self.is_listening:
            return True
            
        try:
            # Create recognizer
            self.recognizer = NSSpeechRecognizer.alloc().init()
            
            if self.recognizer is None:
                print("[Voice] Failed to create NSSpeechRecognizer")
                return False
            
            # Allow listening even when app is not in foreground
            self.recognizer.setListensInForegroundOnly_(False)
            
            # Try to hide the feedback icon/window
            # Setting empty string for title to minimize UI
            self.recognizer.setDisplayedCommandsTitle_('')
            
            # Don't block other recognizers
            self.recognizer.setBlocksOtherRecognizers_(False)
            
            # Set up delegate with callback
            self.delegate = VoiceRecognizerDelegate.alloc().initWithCallback_(self._on_wake_word)
            self.recognizer.setDelegate_(self.delegate)
            
            # Only set wake words - no command phrases
            self.recognizer.setCommands_(self.WAKE_WORDS)
            
            # Start listening
            self.recognizer.startListening()
            self.is_listening = True
            
            print(f"[Voice] Wake word listener started. Say: {', '.join(self.WAKE_WORDS)}")
            return True
            
        except Exception as e:
            print(f"[Voice] Failed to start: {e}")
            return False
            
    def stop(self):
        """Stop listening for wake words."""
        if not self.is_listening:
            return
            
        try:
            if self.recognizer:
                self.recognizer.stopListening()
                self.recognizer.setDelegate_(None)
                self.recognizer = None
            self.delegate = None
            self.is_listening = False
            print("[Voice] Wake word listener stopped")
        except Exception as e:
            print(f"[Voice] Failed to stop: {e}")
            
    def _on_wake_word(self, command: str):
        """Handle recognized wake word."""
        print(f"[Voice] Wake word detected: {command}")
        self.wake_word_detected.emit()
        
    def is_available(self) -> bool:
        """Check if voice recognition is available on this system."""
        try:
            test_recognizer = NSSpeechRecognizer.alloc().init()
            if test_recognizer:
                return True
            return False
        except:
            return False


class MacOSDictation(QObject):
    """
    Trigger macOS system Dictation for speech-to-text.
    Uses AppleScript to trigger system dictation.
    
    Requirements:
    - macOS Dictation must be enabled in System Preferences
    - Accessibility permissions may be required
    """
    
    # Signal emitted when dictation starts
    dictation_started = pyqtSignal()
    
    # Signal emitted when dictation ends
    dictation_ended = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_active = False
        
    def toggle_dictation(self):
        """Toggle macOS dictation on/off using AppleScript keystroke simulation."""
        try:
            import subprocess
            
            # Use AppleScript to simulate pressing Fn twice
            # This triggers the default dictation shortcut
            script = '''
            tell application "System Events"
                -- Simulate pressing the dictation shortcut (default: press Fn twice)
                -- We use key code 63 for the Fn key
                key code 63
                delay 0.1
                key code 63
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"[Dictation] AppleScript error: {result.stderr}")
                # Try alternative method using keystroke
                return self._try_keystroke_method()
            
            self._is_active = not self._is_active
            
            if self._is_active:
                print("[Dictation] Started - speak now...")
                self.dictation_started.emit()
            else:
                print("[Dictation] Stopped")
                self.dictation_ended.emit()
                
            return True
            
        except Exception as e:
            print(f"[Dictation] Failed to toggle: {e}")
            return False
    
    def _try_keystroke_method(self):
        """Alternative method using direct keystroke for dictation."""
        try:
            import subprocess
            # Try Control+Command+Space as alternative dictation shortcut
            script = '''
            tell application "System Events"
                keystroke " " using {control down, command down}
            end tell
            '''
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self._is_active = not self._is_active
                if self._is_active:
                    print("[Dictation] Started via Control+Command+Space")
                    self.dictation_started.emit()
                else:
                    print("[Dictation] Stopped")
                    self.dictation_ended.emit()
                return True
            else:
                print(f"[Dictation] Alternative method also failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"[Dictation] Alternative method failed: {e}")
            return False
    
    def start(self):
        """Start dictation if not already active."""
        if not self._is_active:
            return self.toggle_dictation()
        return True
        
    def stop(self):
        """Stop dictation if active."""
        if self._is_active:
            return self.toggle_dictation()
        return True
        
    @property
    def is_active(self):
        return self._is_active
