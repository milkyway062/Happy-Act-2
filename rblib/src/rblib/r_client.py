import ctypes
from ctypes import wintypes
import winreg
import os
import subprocess
import signal
import uuid
import requests
import re
from .r_account import Account
import time
# DLLs
user32 = ctypes.windll.user32
psapi = ctypes.windll.psapi
kernel = ctypes.windll.kernel32
#Structures
class Rect(ctypes.Structure):
    """
    Represents a rectangle returned by the Windows API.

    Attributes:
        x (int): The left coordinate of the rectangle.
        y (int): The top coordinate of the rectangle.
        w (int): The right coordinate of the rectangle.
        h (int): The bottom coordinate of the rectangle.
    """
    _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long), ('w', ctypes.c_long), ('h', ctypes.c_long)]


class RobloxClient():
    """
    Represents the Roblox desktop client and provides utilities for
    retrieving process/window information, launching Roblox, and joining
    games with or without an account-specific authentication ticket.
    """

    def __init__(self, cookie: str | Account | None = None):
        """
        Initialize a RobloxClient instance.

        Args:
            cookie (str | Account | None):
                Either:
                - a raw .ROBLOSECURITY cookie string,
                - an Account object containing a cookie,
                - or None to use standard non-account-specific joins.

        Notes:
            - If a cookie or Account is provided, account-specific joining is enabled.
            - If None is provided, joins use the standard roblox:// protocol format.
        """
        self.accountSpecific = False
        if cookie is not None:
            self.accountSpecific = True
            if isinstance(cookie, Account):
                self.cookie = cookie.UserCookie
            else:
                self.cookie = cookie
    def _generate_csrf(self) -> str:
        """
        Generate a CSRF token for authenticated Roblox web requests.

        Returns:
            str:
                The X-CSRF-TOKEN required for authenticated Roblox API requests.

        Notes:
            This sends a logout request to Roblox to force a CSRF token response.
        """
        r = requests.post("https://auth.roblox.com/v2/logout",cookies={".ROBLOSECURITY": self.cookie})
        csrf_token = r.headers.get("X-CSRF-TOKEN")
        if not csrf_token:
            print("no csrf")
            return f"error creating ticket : {r.status_code}"

        return csrf_token
    def _generate_ticket(self) -> str:
        """
        Generate a Roblox authentication ticket for launching an authenticated
        Roblox client session.

        Returns:
            str:
                The rbx-authentication-ticket used in Roblox launch protocol URLs.

        Notes:
            Requires a valid .ROBLOSECURITY cookie
        """
        csrf_token = self._generate_csrf()
        ticket_headers = {
                "X-CSRF-TOKEN": csrf_token,
                "Referer": "www.roblox.com", 
                "Content-Type": "application/json",
                "RBX-For-Gameauth": "true" 
        }
        ticket = requests.post("https://auth.roblox.com/v1/authentication-ticket", headers=ticket_headers, cookies={".ROBLOSECURITY": self.cookie}).headers.get("rbx-authentication-ticket")
        if not ticket:
            return f"error creating ticket : {ticket.status_code}"
        return ticket
    def _fetch_acesscode(self,place_id, link_code):
        """
        Resolve a private server link code into a private server access code.

        Args:
            place_id (int):
                The Roblox place ID of the game.
            link_code (str | int):
                The private server link code.

        Returns:
            str | None:
                The private server access code if found, otherwise None.

        Notes:
            This scrapes the game page HTML and extracts the access code from
            the joinPrivateGame(...) call.
        """
        url = f"https://www.roblox.com/games/{place_id}/?privateServerLinkCode={link_code}"
        jar = requests.cookies.RequestsCookieJar()
        jar.set(".ROBLOSECURITY", self.cookie, domain=".roblox.com", path="/")
        r = requests.get(url, cookies=jar)
        pattern = r"joinPrivateGame\(\s*\d+,\s*'([0-9a-fA-F\-]+)'\s*,\s*'([0-9]+)'\s*\)"
        match = re.search(pattern, r.text)
        if not match:
            return None  
        access_code = match.group(1)
        return access_code
    
    def _build_protocol_url(self,ticket: str, place_id: int, access_code=None, link_code=None, job_id=None, join_vip=False) -> str:
        """
        Build a Roblox authenticated launch protocol URL.

        Args:
            ticket (str):
                The Roblox authentication ticket.
            place_id (int):
                The Roblox place ID to join.
            access_code (str | None):
                The private server access code used for VIP/private server joins.
            link_code (str | None):
                The private server link code used for VIP/private server joins.
            job_id (str | int | None):
                The target server job ID for direct server joins.
            join_vip (bool):
                Whether to build a private server join URL.

        Returns:
            str:
                A fully formatted roblox-player launch protocol URL.

        Notes:
            - If join_vip is True, a RequestPrivateGame URL is built.
            - Otherwise, a RequestGame or RequestGameJob URL is built.
        """
        base = "https%3A%2F%2Fassetgame.roblox.com%2Fgame%2FPlaceLauncher.ashx"
        if join_vip:
            return (
                f"roblox-player:1+launchmode:play"
                f"+gameinfo:{ticket}"
                f"+placelauncherurl:{base}"
                f"%3Frequest%3DRequestPrivateGame"
                f"%26placeId%3D{place_id}"
                f"%26accessCode%3D{access_code}"
                f"%26linkCode%3D{link_code}"
            )
        job_suffix = "" if not job_id else f"Job%26gameId%3D{job_id}"
        return (
            f"roblox-player:1+launchmode:play"
            f"+gameinfo:{ticket}"
            f"+placelauncherurl:{base}"
            f"%3Frequest%3DRequestGame{job_suffix}"
            f"%26browserTrackerId%3D{uuid.uuid4()}"
            f"%26placeId%3D{place_id}"
            f"%26isPlayTogetherGame%3Dfalse"
        )
    def wait_for_window(self, timeout: float = 15.0, interval: float = 0.1) -> bool:
        """
        Wait until the Roblox window exists (HWND becomes valid).

        Args:
            timeout (float, optional): Maximum number of seconds to wait. Defaults to 15.0.
            interval (float, optional): Time in seconds between checks. Defaults to 0.1.

        Returns:
            bool: True if the window appeared within the timeout, False otherwise.

        Notes:
            This is useful because the Roblox process may start before its window is created.
        """
        start_time = time.time()
        while self.hwnd is None:
            if time.time() - start_time > timeout:
                return False
            time.sleep(interval)
        return True
    @property
    def is_running(self) -> bool:
        return self.pid is not None
    @property
    def pid(self):
        """
        Get the process ID of the currently running Roblox client.

        Returns:
            int | None:
                The process ID of Roblox if found, otherwise None.
        """
        return get_roblox_pid()

    @property
    def exe_path(self):
        """
        Get the executable path of the Roblox client.

        Returns:
            str:
                The full path to the Roblox executable.
        """
        return get_roblox_path()

    @property
    def hwnd(self):
        """
        Get the window handle of the currently running Roblox client.

        Returns:
            int | None:
                The HWND of the Roblox window if found, otherwise None.
        """
        return get_roblox_hwnd()

    @property
    def geometry(self) -> Rect:
        """
        Get the geometry of the Roblox window.

        Returns:
            Rect:
                A Rect containing (x, y, w, h).

        Raises:
            TypeError:
                If Roblox is not open and no valid HWND is found.
        """
        return get_geometry(self.hwnd)

    def join(self, placeId: int, jobId: int | str = "", psLinkCode: int | str = "") -> subprocess.Popen:
        """
        Launch Roblox and join a place, optionally targeting a specific
        server instance or private server link code.

        Args:
            placeId (int):
                The Roblox place ID to join.
            jobId (int | str):
                The server job ID to join directly. If provided, this takes
                priority over psLinkCode.
            psLinkCode (int | str):
                The private server link code to use when joining a private server.

        Returns:
            subprocess.Popen:
                The spawned Roblox process object.

        Notes:
            - If account-specific joining is enabled, an authenticated launch URL
            is built using a Roblox authentication ticket.
            - If psLinkCode is provided, a private server join is attempted.
            - If jobId is provided, a direct server join is attempted.
            - If neither is provided, a normal public server join is used.
        """
        if self.accountSpecific:
            if psLinkCode != "":
                return subprocess.Popen([self.exe_path, self._build_protocol_url(ticket=self._generate_ticket(),place_id=placeId,access_code=self._fetch_acesscode(place_id=placeId,link_code=psLinkCode),link_code=psLinkCode,join_vip=True)])
            elif jobId != "":
                return subprocess.Popen([self.exe_path, self._build_protocol_url(ticket=self._generate_ticket(),place_id=placeId,job_id=jobId)])
            else:
                return subprocess.Popen([self.exe_path, self._build_protocol_url(ticket=self._generate_ticket(),place_id=placeId)])
        else:
            if jobId == "":
                join_string = f"roblox://placeId={placeId}&linkCode={psLinkCode}"
            else:
                join_string = f"roblox://placeId={placeId}&serverJobId={jobId}"
            return subprocess.Popen([self.exe_path, join_string])

    def close(self):
        """
        Close the currently running Roblox client process.

        Raises:
            TypeError:
                If Roblox is not running and pid is None.
        """
        os.kill(self.pid, signal.SIGTERM)

    def spawn(self) -> subprocess.Popen:
        """
        Launch a fresh Roblox client process.

        Returns:
            subprocess.Popen:
                The spawned Roblox process object.
        """
        return subprocess.Popen([self.exe_path])


def get_roblox_path() -> str:
    """
    Get the Roblox executable path from the Windows registry.

    Returns:
        str:
            The full path to the Roblox executable.

    Raises:
        OSError:
            If the registry key cannot be opened or read.
    """
    HKCU = winreg.HKEY_CURRENT_USER
    r_command = r"Software\Classes\roblox-player\shell\open\command"
    key = winreg.OpenKey(HKCU, r_command, access=winreg.KEY_READ)
    value, _ = winreg.QueryValueEx(key, None)
    winreg.CloseKey(key)
    return value.split(" ")[0].replace("\"", "")


def get_roblox_pid() -> int:
    """
    Find the process ID of the running Roblox client by matching the
    executable path against all running processes.

    Returns:
        int | None:
            The Roblox process ID if found, otherwise None.

    Raises:
        OSError:
            If EnumProcesses fails.
    """
    roblox_path = get_roblox_path()
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    proc_ids = (wintypes.DWORD * 4096)()
    proc_size = wintypes.DWORD()

    if not psapi.EnumProcesses(proc_ids, ctypes.sizeof(proc_ids), ctypes.byref(proc_size)):
        raise OSError("EnumProcesses failed. Windows error code: {}".format(ctypes.GetLastError()))

    num_proc = proc_size.value // ctypes.sizeof(wintypes.DWORD)
    proc_pids = proc_ids[:num_proc]

    for pid in proc_pids:
        process_handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not process_handle:
            continue

        buffer = ctypes.create_unicode_buffer(wintypes.MAX_PATH*2)
        size = wintypes.DWORD(len(buffer))
        kernel.QueryFullProcessImageNameW(process_handle, 0, buffer, ctypes.byref(size))
        if buffer.value == roblox_path:
            kernel.CloseHandle(process_handle)
            return pid
        kernel.CloseHandle(process_handle)
    return None


def get_roblox_hwnd() -> int:
    """
    Find the top-level window handle of the running Roblox client.

    Returns:
        int | None:
            The Roblox window handle if found, otherwise None.
    """
    hwnds = []
    r_pid = get_roblox_pid()

    def hwnd_iter(hwnd, lparam):
        hwnds.append(hwnd)
        return True

    enumWindows = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    hwnd_callback = enumWindows(hwnd_iter)
    user32.EnumWindows(hwnd_callback, 5)

    for hwnd in hwnds:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == r_pid:
            return hwnd
    return None

def hold_singletonMutex():
    """
    Attempt to acquire the Roblox singleton mutex.

    Returns:
        bool:
            True if the mutex was acquired successfully, otherwise False.

    Notes:
        Roblox uses a singleton mutex to prevent multiple client instances.
        Holding this mutex can be used to block Roblox from acquiring it.

        This does not bypass the teleportation restriction, which only allows
        the most recently launched instance to teleport.

        If you need teleportation on multiple clients, run each client under a
        different Windows user account.
    """
    R_Mutex = "ROBLOX_singletonMutex"

    mutex = kernel.CreateMutexW(None, False, R_Mutex)
    WAIT_TIMEOUT = 0x102

    result = kernel.WaitForSingleObject(mutex, 0)

    if result == WAIT_TIMEOUT:
        print("Failed to create mutex.")
        return False

    print("Created mutex")
    return True

def focus_roblox_window(x: int = 15, y: int = 15, w: int = 800, h: int = 600) -> bool:
    """
    Bring the Roblox window to the foreground, move it to (x, y), and resize to (w, h).
    Call at macro startup to ensure all window-relative coordinates are valid.
    Returns True if window was found and repositioned.
    """
    hwnd = get_roblox_hwnd()
    if hwnd is None:
        return False
    SWP_NOZORDER = 0x0004
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE — unminimize if needed
    user32.SetForegroundWindow(hwnd)
    user32.SetWindowPos(hwnd, 0, x, y, w, h, SWP_NOZORDER)
    return True


def get_geometry(hwnd) -> Rect:
    """
    Get the screen-space rectangle of a window.

    Args:
        hwnd (int):
            The window handle to query.

    Returns:
        Rect:
            A Rect containing (left, top, right, bottom) coordinates.

    Notes:
        The returned Rect uses raw GetWindowRect values.
        Width and height must be calculated manually if needed.
    """
    rect = Rect()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    rect.w -= rect.x
    rect.h -= rect.y
    return rect
