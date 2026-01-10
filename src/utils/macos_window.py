"""
macOS-specific window utilities for Qt applications
"""


def exclude_window_from_mission_control(qt_window):
    """
    Exclude a Qt window from Mission Control/Exposé on macOS.
    
    This prevents the window from appearing in Mission Control overview,
    eliminating ghost outlines that can appear with transparent windows.
    
    Args:
        qt_window: The Qt window object (should have a winId() method)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import objc
        from AppKit import NSView
        from ctypes import c_void_p
        
        # Get NSView from Qt widget's winId
        window_id = int(qt_window.winId())
        ns_view = objc.objc_object(c_void_p=window_id)
        
        if ns_view:
            # Get NSWindow from NSView
            ns_window = ns_view.window()
            
            if ns_window:
                print(f"[VCat] Found NSWindow: {ns_window}")
                # NSWindowCollectionBehaviorStationary = 1 << 4
                # Makes window not appear in Mission Control/Spaces overview
                ns_window.setCollectionBehavior_(1 << 4)
                
                # Also exclude from window menu
                ns_window.setExcludedFromWindowsMenu_(True)
                
                print("[VCat] Window excluded from Mission Control via NSWindow")
                return True
            else:
                print("[VCat] NSView.window() returned None")
                return False
        else:
            print("[VCat] Could not get NSView from winId")
            return False
            
    except Exception as e:
        import traceback
        print(f"[VCat] Could not exclude from Mission Control: {e}")
        print(f"[VCat] Traceback: {traceback.format_exc()}")
        return False
