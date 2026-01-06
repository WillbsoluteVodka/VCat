"""
macOS permission utilities for VCat.
Handles microphone permission checking and requesting.
"""

import subprocess
from typing import Literal

PermissionStatus = Literal['authorized', 'denied', 'not_determined', 'restricted', 'unknown']


def check_microphone_permission() -> PermissionStatus:
    """
    Check microphone permission status on macOS.
    
    Returns:
        'authorized' - Permission granted
        'denied' - Permission denied by user
        'not_determined' - Not yet requested
        'restricted' - System restriction (parental controls, etc.)
        'unknown' - Could not determine status
    """
    try:
        from AVFoundation import AVCaptureDevice, AVMediaTypeAudio
        
        status = AVCaptureDevice.authorizationStatusForMediaType_(AVMediaTypeAudio)
        
        # AVAuthorizationStatus values:
        # 0 = notDetermined
        # 1 = restricted  
        # 2 = denied
        # 3 = authorized
        
        status_map = {
            0: 'not_determined',
            1: 'restricted',
            2: 'denied',
            3: 'authorized',
        }
        
        return status_map.get(status, 'unknown')
        
    except ImportError:
        # AVFoundation not available, try alternative method
        return _check_permission_via_sounddevice()
    except Exception as e:
        print(f"[Permissions] Error checking microphone permission: {e}")
        return 'unknown'


def _check_permission_via_sounddevice() -> PermissionStatus:
    """Alternative permission check by trying to access microphone."""
    try:
        import sounddevice as sd
        
        # Try to query devices - this may fail if permission denied
        devices = sd.query_devices()
        
        # Check if any input device is available
        input_devices = [d for d in devices if d.get('max_input_channels', 0) > 0]
        
        if input_devices:
            return 'authorized'
        else:
            return 'denied'
            
    except Exception:
        return 'unknown'


def request_microphone_permission(callback=None) -> bool:
    """
    Request microphone permission on macOS.
    
    This will trigger the system permission dialog if permission
    has not been requested before.
    
    Args:
        callback: Optional callback function called with (granted: bool)
        
    Returns:
        True if permission was already granted or request was initiated,
        False if permission was denied or request failed.
    """
    try:
        from AVFoundation import AVCaptureDevice, AVMediaTypeAudio
        
        current_status = check_microphone_permission()
        
        if current_status == 'authorized':
            if callback:
                callback(True)
            return True
            
        if current_status in ('denied', 'restricted'):
            if callback:
                callback(False)
            return False
        
        # Request permission
        def completion_handler(granted):
            print(f"[Permissions] Microphone permission {'granted' if granted else 'denied'}")
            if callback:
                callback(granted)
        
        AVCaptureDevice.requestAccessForMediaType_completionHandler_(
            AVMediaTypeAudio,
            completion_handler
        )
        
        return True
        
    except ImportError:
        # AVFoundation not available, try to trigger permission via recording
        return _request_permission_via_sounddevice(callback)
    except Exception as e:
        print(f"[Permissions] Error requesting microphone permission: {e}")
        if callback:
            callback(False)
        return False


def _request_permission_via_sounddevice(callback=None) -> bool:
    """Alternative permission request by trying to record."""
    try:
        import sounddevice as sd
        import numpy as np
        
        # Try to record a tiny sample - this triggers permission dialog
        duration = 0.1  # 100ms
        sample_rate = 16000
        
        try:
            audio = sd.rec(int(duration * sample_rate), 
                          samplerate=sample_rate, 
                          channels=1, 
                          dtype='float32')
            sd.wait()
            
            if callback:
                callback(True)
            return True
            
        except sd.PortAudioError:
            if callback:
                callback(False)
            return False
            
    except Exception as e:
        print(f"[Permissions] Alternative permission request failed: {e}")
        if callback:
            callback(False)
        return False


def is_first_launch() -> bool:
    """Check if this is the first launch of VCat."""
    import os
    
    config_dir = os.path.expanduser("~/.vcat")
    onboarding_flag = os.path.join(config_dir, ".onboarding_complete")
    
    return not os.path.exists(onboarding_flag)


def mark_onboarding_complete():
    """Mark the onboarding as complete."""
    import os
    
    config_dir = os.path.expanduser("~/.vcat")
    os.makedirs(config_dir, exist_ok=True)
    
    onboarding_flag = os.path.join(config_dir, ".onboarding_complete")
    
    with open(onboarding_flag, 'w') as f:
        f.write("1")
    
    print("[Permissions] Onboarding marked as complete")


def reset_onboarding():
    """Reset onboarding for testing purposes."""
    import os
    
    onboarding_flag = os.path.expanduser("~/.vcat/.onboarding_complete")
    
    if os.path.exists(onboarding_flag):
        os.remove(onboarding_flag)
        print("[Permissions] Onboarding reset")
