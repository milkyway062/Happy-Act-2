import ctypes
import time
import atexit
from .r_client import get_roblox_hwnd, get_geometry
#Type
INPUT_KEYBOARD = 1
INPUT_MOUSE = 0
#Keyboard
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
#Mouse
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_ABSOLUTE = 0x8000

SendInput = ctypes.windll.user32.SendInput
ulong_pointer = ctypes.POINTER(ctypes.c_ulong)
# Codes
SCANCODES = {
    "escape": 0x01,
    "1": 0x02,
    "2": 0x03,
    "3": 0x04,
    "4": 0x05,
    "5": 0x06,
    "6": 0x07,
    "7": 0x08,
    "8": 0x09,
    "9": 0x0A,
    "0": 0x0B,
    "minus": 0x0C,
    "equals": 0x0D,
    "backspace": 0x0E,
    "tab": 0x0F,
    "q": 0x10,
    "w": 0x11,
    "e": 0x12,
    "r": 0x13,
    "t": 0x14,
    "y": 0x15,
    "u": 0x16,
    "i": 0x17,
    "o": 0x18,
    "p": 0x19,
    "bracketLeft": 0x1A,
    "bracketRight": 0x1B,
    "enter": 0x1C,
    "controlLeft": 0x1D,
    "a": 0x1E,
    "s": 0x1F,
    "d": 0x20,
    "f": 0x21,
    "g": 0x22,
    "h": 0x23,
    "j": 0x24,
    "k": 0x25,
    "l": 0x26,
    "semicolon": 0x27,
    "apostrophe": 0x28,
    "grave": 0x29,
    "shiftLeft": 0x2A,
    "backslash": 0x2B,
    "z": 0x2C,
    "x": 0x2D,
    "c": 0x2E,
    "v": 0x2F,
    "b": 0x30,
    "n": 0x31,
    "m": 0x32,
    "comma": 0x33,
    "period": 0x34,
    "slash": 0x35,
    "shiftRight": 0x36,
    "numpad_multiply": 0x37,
    "altLeft": 0x38,
    "space": 0x39,
    "capsLock": 0x3A,
    "f1": 0x3B,
    "f2": 0x3C,
    "f3": 0x3D,
    "f4": 0x3E,
    "f5": 0x3F,
    "f6": 0x40,
    "f7": 0x41,
    "f8": 0x42,
    "f9": 0x43,
    "f10": 0x44,
    "numLock": 0x45,
    "scrollLock": 0x46,
    "numpad_7": 0x47,
    "numpad_8": 0x48,
    "numpad_9": 0x49,
    "numpad_minus": 0x4A,
    "numpad_4": 0x4B,
    "numpad_5": 0x4C,
    "numpad_6": 0x4D,
    "numpad_plus": 0x4E,
    "numpad_1": 0x4F,
    "numpad_2": 0x50,
    "numpad_3": 0x51,
    "numpad_0": 0x52,
    "numpad_period": 0x53,
    "alt_printScreen": 0x54,
    "bracketAngle": 0x56,
    "f11": 0x57,
    "f12": 0x58,
    "oem_1": 0x5A,
    "oem_2": 0x5B,
    "oem_3": 0x5C,
    "eraseEOF": 0x5D,
    "oem_4": 0x5E,
    "oem_5": 0x5F,
    "zoom": 0x62,
    "help": 0x63,
    "f13": 0x64,
    "f14": 0x65,
    "f15": 0x66,
    "f16": 0x67,
    "f17": 0x68,
    "f18": 0x69,
    "f19": 0x6A,
    "f20": 0x6B,
    "f21": 0x6C,
    "f22": 0x6D,
    "f23": 0x6E,
    "oem_6": 0x6F,
    "katakana": 0x70,
    "oem_7": 0x71,
    "f24": 0x76,
    "sbcschar": 0x77,
    "convert": 0x79,
    "nonconvert": 0x7B,
    "media_previous": 0xE010,
    "media_next": 0xE019,
    "numpad_enter": 0xE01C,
    "controlRight": 0xE01D,
    "volume_mute": 0xE020,
    "launch_app2": 0xE021,
    "media_play": 0xE022,
    "media_stop": 0xE024,
    "volume_down": 0xE02E,
    "volume_up": 0xE030,
    "browser_home": 0xE032,
    "numpad_divide": 0xE035,
    "printScreen": 0xE037,
    "altRight": 0xE038,
    "cancel": 0xE046,
    "home": 0xE047,
    "arrowUp": 0xE048,
    "pageUp": 0xE049,
    "arrowLeft": 0xE04B,
    "arrowRight": 0xE04D,
    "end": 0xE04F,
    "arrowDown": 0xE050,
    "pageDown": 0xE051,
    "insert": 0xE052,
    "delete": 0xE053,
    "metaLeft": 0xE05B,
    "metaRight": 0xE05C,
    "application": 0xE05D,
    "power": 0xE05E,
    "sleep": 0xE05F,
    "wake": 0xE063,
    "browser_search": 0xE065,
    "browser_favorites": 0xE066,
    "browser_refresh": 0xE067,
    "browser_stop": 0xE068,
    "browser_forward": 0xE069,
    "browser_back": 0xE06A,
    "launch_app1": 0xE06B,
    "launch_email": 0xE06C,
    "launch_media": 0xE06D,
    "pause": 0xE11D45,
}

key_cache = {}

class KeyboardInput(ctypes.Structure):
    _fields_ = [("wVk",ctypes.c_ushort),("wScan",ctypes.c_ushort),("dwFlags",ctypes.c_ulong),("time",ctypes.c_ulong),("dwExtraInfo",ulong_pointer)]
class MouseInput(ctypes.Structure):
    _fields_ = [("dx",ctypes.c_long),("dy",ctypes.c_long),("mouseData",ctypes.c_ulong),("dwFlags",ctypes.c_ulong),("time",ctypes.c_ulong),("dwExtraInfo",ulong_pointer)]
class InputUnion(ctypes.Union):
    _fields_ = [("ki", KeyboardInput), ("mi", MouseInput)]
class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("iu",InputUnion)]

def ResolveKey(Key: int | str) -> tuple[int,int]:
    """
    Resolve a key into a scan code and any additional keyboard flags.

    Returns:
        tuple[int, int]:
            (scan_code, extra_flags)
    """
    if isinstance(Key, str):
        Scancode = SCANCODES.get(Key.lower())
        if Scancode is None:
            raise Exception(f"Unknown key alias: {Key}")
    else:
        Scancode = Key
    flags = KEYEVENTF_SCANCODE
    if Scancode > 0xFF:
        flags|=KEYEVENTF_EXTENDEDKEY
        Scancode&=0xFF # cut extended
    return Scancode, flags

def KeyDown(Key: int | str) -> None:
    """
    Hold down a key using its scan code.

    Args:
        key (int | str):
            Either:
            - an integer scan code, or
            - a recognized string alias that maps to a scan code.
    Raises:
        KeyNotFound: If Key is a string and is not a valid recognized alias.
    """
    scKey, flags = ResolveKey(Key)
    extra = ctypes.c_ulong(0)
    _iu = InputUnion()
    _iu.ki = KeyboardInput(0,scKey, flags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(INPUT_KEYBOARD),_iu)
    SendInput(1,ctypes.pointer(x),ctypes.sizeof(x))
    key_cache[scKey] = True

def KeyUp(Key: int | str) -> None:
    """
    Release a key using its scan code.

    Args:
        key (int | str):
            Either:
            - an integer scan code, or
            - a recognized string alias that maps to a scan code.
    
    Raises:
        KeyNotFound: If Key is a string and is not a valid recognized alias.
    """
    scKey, flags = ResolveKey(Key)
    extra = ctypes.c_ulong(0)
    _iu = InputUnion()
    _iu.ki = KeyboardInput(0,scKey, flags | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(INPUT_KEYBOARD),_iu)
    SendInput(1,ctypes.pointer(x),ctypes.sizeof(x))
    key_cache.pop(scKey,None)
    
def PressKey(Key: int | str, Delay: float=0.1, numTimes: int=1, interval: float=0.0):
    """
    Press a key using its scan code, with optional repeats and delays.

    Args:
        Key (int | str):
            Either:
            - an integer scan code, or
            - a recognized string alias that maps to a scan code.
        Delay (float):
            The amount of time in seconds to wait before releasing the key
            after each press.
        numTimes (int | None):
            The number of times to press the key.
        interval (float | None):
            The amount of time in seconds to wait between repeated presses.

    Raises:
        KeyNotFound:
            If Key is a string and is not a valid recognized alias.
    """
    for _ in range(numTimes):
        KeyDown(Key)
        time.sleep(Delay)
        KeyUp(Key)
        time.sleep(interval)

def PositionVerify() -> None:
    '''
    Updates mouse position on the roblox client by moving the mouse up and down 1 pixel using user32.mousevent.
    '''
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, 0, 1, 0, 0)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, 0, -1, 0, 0)

def MoveTo(x: int,y: int) -> None:
    '''
    Moves the cursor to a given location

    Args:
        x (int): x coordinate on the display.
        y (int): y coordinate on the display.
    '''
    extra = ctypes.c_ulong(0)

    sw = ctypes.windll.user32.GetSystemMetrics(0)
    sh = ctypes.windll.user32.GetSystemMetrics(1)

    abs_x = int(x * 65535 / (sw - 1))
    abs_y = int(y * 65535 / (sh - 1))

    _iu = InputUnion()
    _iu.mi = MouseInput(abs_x,abs_y,0,MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
    UserInput = Input(ctypes.c_ulong(INPUT_MOUSE),_iu)
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))
    PositionVerify()

def absClick(x: int,y: int,delay: float) -> None:
    '''
    Move the cursor to a given position, wait for a delay, then clicks

    Args:
        x (int): x coordinate on the display.
        y (int): y coordinate on the display.
        delay (float): How long in seconds it should wait before clicking
    '''
    extra = ctypes.c_ulong(0)
    MoveTo(x,y)
    time.sleep(delay)
    _iu = InputUnion()
    _iu.mi = MouseInput(0,0,0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
    UserInput = Input(ctypes.c_ulong(INPUT_MOUSE),_iu)
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))
    UserInput.iu.mi.dwFlags=MOUSEEVENTF_LEFTUP
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))
def absRightClick(x: int,y: int,delay: float) -> None:
    '''
    Move the cursor to a given position, wait for a delay, then right clicks

    Args:
        x (int): x coordinate on the display.
        y (int): y coordinate on the display.
        delay (float): How long in seconds it should wait before clicking
    '''
    extra = ctypes.c_ulong(0)
    MoveTo(x,y)
    time.sleep(delay)
    _iu = InputUnion()
    _iu.mi = MouseInput(0,0,0, MOUSEEVENTF_RIGHTDOWN, 0, ctypes.pointer(extra))
    UserInput = Input(ctypes.c_ulong(INPUT_MOUSE),_iu)
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))
    UserInput.iu.mi.dwFlags=MOUSEEVENTF_RIGHTUP
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))

def absCustomClick(x: int, y: int, dwFlagsDown: list, dwFlagsUp: list, delay: float) -> None:
    """
    Move the cursor to a given position, wait for a delay, then send a custom
    mouse button press and release using the provided mouse event flags.

    Args:
        x (int):
            The x-coordinate on the screen to move the cursor to.
        y (int):
            The y-coordinate on the screen to move the cursor to.
        dwFlagsDown (list):
            A list of mouse event flags to combine and send for the mouse
            button press event.
        dwFlagsUp (list):
            A list of mouse event flags to combine and send for the mouse
            button release event.
        delay (float):
            The amount of time in seconds to wait after moving the cursor
            before sending the click.

    Notes:
        - All flags in dwFlagsDown are combined using bitwise OR into a single
          press-event flag value.
        - All flags in dwFlagsUp are combined using bitwise OR into a single
          release-event flag value.
    """
    flagDown = 0
    for flag in dwFlagsDown:
        flagDown|=flag
    flagUp = 0
    for flag in dwFlagsUp:
        flagUp|=flag
    extra = ctypes.c_ulong(0)
    MoveTo(x,y)
    time.sleep(delay)
    _iu = InputUnion()
    _iu.mi = MouseInput(0,0,0, flagDown, 0, ctypes.pointer(extra))
    UserInput = Input(ctypes.c_ulong(INPUT_MOUSE),_iu)
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))
    UserInput.iu.mi.dwFlags=flagUp
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))
def Click(x: int,y: int,delay: float) -> None:
    '''
    Move the cursor to a given position relative to the roblox window, wait for a delay, then clicks

    Args:
        x (int): x coordinate on the display.
        y (int): y coordinate on the display.
        delay (float): How long in seconds it should wait before clicking
    '''
    extra = ctypes.c_ulong(0)
    geometry = get_geometry(get_roblox_hwnd())
    MoveTo(x+geometry.x,y+geometry.y)
    time.sleep(delay)
    _iu = InputUnion()
    _iu.mi = MouseInput(0,0,0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
    UserInput = Input(ctypes.c_ulong(INPUT_MOUSE),_iu)
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))
    UserInput.iu.mi.dwFlags=MOUSEEVENTF_LEFTUP
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))
def RightClick(x: int,y: int,delay: float) -> None:
    '''
    Move the cursor to a given position relative to the roblox window, wait for a delay, then right clicks

    Args:
        x (int): x coordinate on the display.
        y (int): y coordinate on the display.
        delay (float): How long in seconds it should wait before clicking
    '''
    extra = ctypes.c_ulong(0)
    
    geometry = get_geometry(get_roblox_hwnd())
    MoveTo(x+geometry.x,y+geometry.y)
    time.sleep(delay)
    _iu = InputUnion()
    _iu.mi = MouseInput(0,0,0, MOUSEEVENTF_RIGHTDOWN, 0, ctypes.pointer(extra))
    UserInput = Input(ctypes.c_ulong(INPUT_MOUSE),_iu)
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))
    UserInput.iu.mi.dwFlags=MOUSEEVENTF_RIGHTUP
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))

def CustomClick(x: int, y: int, dwFlagsDown: list, dwFlagsUp: list, delay: float) -> None:
    """
    Move the cursor to a given position relative to the roblox window, wait for a delay, then send a custom
    mouse button press and release using the provided mouse event flags.

    Args:
        x (int):
            The x-coordinate on the screen to move the cursor to.
        y (int):
            The y-coordinate on the screen to move the cursor to.
        dwFlagsDown (list):
            A list of mouse event flags to combine and send for the mouse
            button press event.
        dwFlagsUp (list):
            A list of mouse event flags to combine and send for the mouse
            button release event.
        delay (float):
            The amount of time in seconds to wait after moving the cursor
            before sending the click.

    Notes:
        - All flags in dwFlagsDown are combined using bitwise OR into a single
          press-event flag value.
        - All flags in dwFlagsUp are combined using bitwise OR into a single
          release-event flag value.
    """
    flagDown = 0
    for flag in dwFlagsDown:
        flagDown|=flag
    flagUp = 0
    for flag in dwFlagsUp:
        flagUp|=flag
    extra = ctypes.c_ulong(0)
    geometry = get_geometry(get_roblox_hwnd())
    MoveTo(x+geometry.x,y+geometry.y)
    time.sleep(delay)
    _iu = InputUnion()
    _iu.mi = MouseInput(0,0,0, flagDown, 0, ctypes.pointer(extra))
    UserInput = Input(ctypes.c_ulong(INPUT_MOUSE),_iu)
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))
    UserInput.iu.mi.dwFlags=flagUp
    SendInput(1,ctypes.pointer(UserInput),ctypes.sizeof(UserInput))

@atexit.register
def cleanup():
    #make sure nothing is held down
    for key in list(key_cache.keys()):
        KeyUp(key)
