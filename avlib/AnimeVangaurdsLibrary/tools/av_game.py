import ctypes
import os
import time
from enum import Enum
from typing import Union

import cv2
import numpy
from numpy.dtypes import BoolDType
from pytesseract.pytesseract import List
from rblib import r_input, r_util
from rblib.r_client import RobloxClient, get_geometry, get_roblox_hwnd

from AnimeVangaurdsLibrary import Game_Settings as GS

from . import state as globalStates
from .state import get_state

global set, state
state = get_state()
set = GS.avgs

cached_wave_numbers = {}

resources = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")


class Map(Enum):
    """
    Enum of map reference images used for automatic spawn positioning.

    Each enum value is the absolute file path to the corresponding map image
    inside the local resources/PosImg directory.

    Attributes:
        ANT_ISLAND: Reference image for Ant Island.
        AOT_BOSS_RAID: Reference image for AOT boss raid.
        BURNING_SPIRIT_TREE: Reference image for Burning Spirit Tree.
        CRYSTAL_CHAPEL: Reference image for Crystal Chapel.
        DOUBLE_DUNGEON: Reference image for Double Dungeon.
        FROZEN_PORT: Reference image for Frozen Port.
        HILL_OF_SWORDS: Reference image for Hill of Swords.
        IMPRISONED_ISLAND: Reference image for Imprisoned Island.
        KUINSHI_PALACE: Reference image for Kuinshi Palace.
        LEBEREO_RAID: Reference image for Lebereo Raid.
        PLANET_NAMEK: Reference image for Planet Namek.
        SABER_BOSS_RAID: Reference image for Saber boss raid.
        SAND_VILLAGE: Reference image for Sand Village.
        SHIBUYA_AFTERMATH: Reference image for Shibuya Aftermath.
        SHINING_CASTLE: Reference image for Shining Castle.
        SPIDER_FOREST: Reference image for Spider Forest.
        SPIRIT_SOCIETY: Reference image for Spirit Society.
    """

    ANT_ISLAND = os.path.join(resources, "PosImg", "Ant_Island.png")
    AOT_BOSS_RAID = os.path.join(resources, "PosImg", "AOT.png")
    BURNING_SPIRIT_TREE = os.path.join(resources, "PosImg", "Burning_Spirit_Tree.png")
    CRYSTAL_CHAPEL = os.path.join(resources, "PosImg", "Crystal_Chapel.png")
    DOUBLE_DUNGEON = os.path.join(resources, "PosImg", "Double_Dungeon.png")
    FROZEN_PORT = os.path.join(resources, "PosImg", "Frozen_Port.png")
    HILL_OF_SWORDS = os.path.join(resources, "PosImg", "Hill_Of_Swords.png")
    IMPRISONED_ISLAND = os.path.join(resources, "PosImg", "Imprisoned_Island.png")
    KUINSHI_PALACE = os.path.join(resources, "PosImg", "Kuinshi_Palace.png")
    LEBEREO_RAID = os.path.join(resources, "PosImg", "Lebereo_Raid.png")
    PLANET_NAMEK = os.path.join(resources, "PosImg", "Planet_Namek.png")
    SABER_BOSS_RAID = os.path.join(resources, "PosImg", "Saber.png")
    SAND_VILLAGE = os.path.join(resources, "PosImg", "Sand_Village.png")
    SHIBUYA_AFTERMATH = os.path.join(resources, "PosImg", "Shibuya_Aftermath.png")
    SHINING_CASTLE = os.path.join(resources, "PosImg", "Shining_Castle.png")
    SPIDER_FOREST = os.path.join(resources, "PosImg", "Spider_Forest.png")
    SPIRIT_SOCIETY = os.path.join(resources, "PosImg", "Spirit_Society.png")


class Areas(Enum):
    """
    Enum of lobby area categories used when navigating to different game modes.

    Attributes:
        STORY: Story mode area.
        LEGEND_STAGE: Legend Stage area.
        RAID: Raid area.
        DUNGEONS: Dungeon area.
        CHALLENGES: Challenge area.
        BOSS_RAID: Boss Raid area.
        ODYSSEY: Odyssey area.
        WORLDLINES: Worldlines area.
        ELEMENTAL_TOWERS: Elemental Towers area.
        WINTER_EVENT: Winter Event area.
        WHITEBEARD: Whitebeard event area.
    """

    STORY = 0
    LEGEND_STAGE = 1
    RAID = 2
    DUNGEONS = 3
    CHALLENGES = 4
    BOSS_RAID = 5
    ODYSSEY = 6
    WORLDLINES = 7
    ELEMENTAL_TOWERS = 8
    WINTER_EVENT = 9
    WHITEBEARD = 10


class Stages(Enum):
    """
    Enum of stage indices used for stage selection in supported areas.

    Notes:
        - Enum values are reused across different area categories.
        - The same numeric value may represent different stages depending on the selected Areas value.
        - These values are primarily intended for use with lobby_path().

    Story Stages:
        PLANET_NAMEK
        SAND_VILLAGE
        DOUBLE_DUNGEON
        SHIBUYA_STATION
        UNDERGROUND_CHURCH
        SPIRIT_SOCIETY
        MARTIAL_ISLAND
        EDGE_OF_HEAVEN
        LEBEREO_RAID
        HILL_OF_SWORDS
        FROZEN_PORT
        DOWNTOWN_TOKYO

    Legend Stages:
        SAND_VILLAGE_L
        DOUBLE_DUNGEON_L
        SHIBUYA_AFTERMATH
        GOLDEN_CASTLE
        KUINSHI_PALACE
        LAND_OF_THE_GODS
        SHINING_CASTLE
        CRYSTAL_CHAPEL
        BURNING_SPIRIT_TREE
        IMPRISONED_ISLAND
        TOKYO_RAILWAY

    Raid Stages:
        SPIDER_FOREST
        TRACKS_AT_THE_EDGE_OF_THE_WORLD
        RUINED_CITY
        HAPPY_FACTORY

    Dungeon Stages:
        ANT_ISLAND
        FROZEN_VOLCANO
        UNDERWORLD
    """

    # Story
    PLANET_NAMEK = 1
    SAND_VILLAGE = 2
    DOUBLE_DUNGEON = 3
    SHIBUYA_STATION = 4
    UNDERGROUND_CHURCH = 5
    SPIRIT_SOCIETY = 6
    MARTIAL_ISLAND = 7
    EDGE_OF_HEAVEN = 8
    LEBEREO_RAID = 9
    HILL_OF_SWORDS = 10
    FROZEN_PORT = 11
    DOWNTOWN_TOKYO = 12

    # LEGEND_STAGES
    SAND_VILLAGE_L = 1
    DOUBLE_DUNGEON_L = 2
    SHIBUYA_AFTERMATH = 3
    GOLDEN_CASTLE = 4
    KUINSHI_PALACE = 5
    LAND_OF_THE_GODS = 6
    SHINING_CASTLE = 7
    CRYSTAL_CHAPEL = 8
    BURNING_SPIRIT_TREE = 9
    IMPRISONED_ISLAND = 10
    TOKYO_RAILWAY = 11

    # RAIDS
    SPIDER_FOREST = 1
    TRACKS_AT_THE_EDGE_OF_THE_WORLD = 2
    RUINED_CITY = 3
    HAPPY_FACTORY = 4

    # DUNGEONS
    ANT_ISLAND = 1
    FROZEN_VOLCANO = 2
    UNDERWORLD = 3


class Card(Enum):
    CHAMP = "Champ"
    EXPLODING = "Exploding"
    IMMUNITY = "Immunity"
    QUAKE = "Quake"
    REVITALIZE = "Revitalize"
    THRICE = "Thrice"
    COOLDOWN = "Cooldown"
    DAMAGE = "Damage"
    DODGE = "Dodge"
    FAST = "Fast"
    FISTICUFFS = "Fisticuffs"
    HARVEST = "Harvest"
    HIGH_CLASS = "High_Class"
    KINGSBURDEN = "KingsBurden"
    LIMITBREAK = "LimitBreak"
    LOOT = "Loot"
    PRECISE = "Percise"
    PRESS_IT = "Press_It"
    RANGE = "Range"
    SLAYER = "Slayer"
    STRONG = "Strong"
    SURGE = "Surge"
    TYRANTDESTROYER = "TyrantDestroyer"
    TYRANT_ARRIVES = "Tyrant_Arrives"


def scroll(notches):
    notch = 120  # 1 notch
    send_input = ctypes.windll.user32.SendInput
    # useless but needed
    extra = ctypes.c_ulong(0)
    _iu = r_input.InputUnion()
    # 0x0800 is the move flag
    _iu.mi = r_input.MouseInput(0, 0, notch * notches, 0x0800, 0, ctypes.pointer(extra))
    user_input = r_input.Input(ctypes.c_ulong(0), _iu)
    send_input(1, ctypes.pointer(user_input), ctypes.sizeof(user_input))


def join_game():
    """
    Join the Anime Vanguards Roblox experience using its place ID.

    Args:
        None

    Returns:
        None
    """

    RobloxClient().join(placeId=16146832113)


def resize_window(base_geometry=(816, 638)):
    """
    Resize the Roblox window to a fixed base resolution while keeping its current position.

    Args:
        base_geometry (tuple[int, int]): Target window width and height.

    Returns:
        None
    """
    hwnd = r_util.get_roblox_hwnd()
    c_geo = r_util.get_geometry(hwnd)
    ctypes.windll.user32.MoveWindow(
        hwnd, c_geo.x, c_geo.y, base_geometry[0], base_geometry[1], True
    )


def run():
    """
    Mark the specified global state as running.

    Args:
        None

    Returns:
        None
    """
    globalStates.update_state(state.name, running=True)


def stop():
    """
    Mark the specified global state as paused.

    Args:
        None

    Returns:
        None
    """
    globalStates.update_state(state.name, paused=True)


def unpause():
    """
    Unpause the specified global state.

    Args:
        None

    Returns:
        None
    """
    globalStates.update_state(state.name, paused=False)


def get_win():
    """
    Get the win flag for the specified global state.

    Args:
        None

    Returns:
        bool: The state's win status.
    """
    return state.win


def get_loss():
    """
    Get the loss flag for the specified global state.

    Args:
        None

    Returns:
        bool: The state's loss status.
    """
    return state.loss


def get_wins():
    """
    Get the total number of wins recorded for the specified global state.

    Args:
        None

    Returns:
        int: Total wins.
    """
    return state.wins


def inc_wins():
    """
    Increments wins value of global state value

    Args:
        None
    Returns:
        int: Total wins.
    """
    state.wins += 1
    return state.wins


def inc_losses():
    """
    Increments losses value of global state value

    Args:
        None

    Returns:
        int: Total wins.
    """
    state.losses += 1
    return state.losses


def get_losses():
    """
    Get the total number of losses recorded for the specified global state.

    Args:
        None

    Returns:
        int: Total losses.
    """
    return state.losses


def get_runtime():
    """
    Get the runtime value for the specified global state.

    Args:
        None

    Returns:
        float | int: The tracked runtime value.
    """
    return state.runtime


def check_failed() -> bool:
    """
    Check whether the current match has been lost.

    Args:
        None

    Returns:
        bool: True if the lose detection pixel matches the configured loss color, otherwise False.
    """
    if r_util.pixelMatchesColor(
        *set.lose_detection_pixel,
        set.lose_detection_color,
        15,
    ):
        state.loss = True
        state.win = False
        return True
    return False


def check_victory() -> bool:
    """
    Check whether the current match has been won.

    Args:
        None

    Returns:
        bool: True if the lose detection pixel no longer matches the configured loss color, otherwise False.
    """
    if not r_util.pixelMatchesColor(
        *set.lose_detection_pixel,
        set.lose_detection_color,
        15,
    ):
        state.loss = False
        state.win = True
        return True
    return False


def check_ended() -> bool:
    """
    Check whether the current match has ended and verify the end screen is visible.

    Args:
        None

    Returns:
        bool: True if the match end pixel is visible and the end screen verification image is found, otherwise False.
    """
    if r_util.pixelMatchesColor(*set.game_end_pixel, (254, 254, 254), 10) and (
        check_victory() or check_failed()
    ):
        if r_util.imageExists(
            os.path.join(resources, "MatchEndVerify.png"),
            0.9,
            region=(88, 255, 190, 56),
        ):
            print("MATCH IS ENDED")
            return True
    return False


def auto_position(
    image_path: str | Map | None = None,
    check_region=None,
    ctm_inputs: dict | None = None,
    restart=True,
    check_for_cards=False,
):
    """
    Reset the camera to spawn, optionally verify the map by image, perform custom right-click inputs,
    and optionally restart the match.

    Args:
        image_path (str | Map | None): Path to a map reference image, a Map enum value, or None.
            If provided, the function waits until the image is detected in the check region after returning to spawn.
        check_region (tuple[int, int, int, int] | None): Region used to search for the map image.
            Defaults to (0, 0, 399, 355) if not provided.
        ctm_inputs (dict[tuple[int, int], float] | None): Optional mapping of right-click positions to delays.
            Each key is a coordinate to right-click, and each value is the time to wait afterward.
        restart (bool): Whether to start and restart the match after positioning is complete.
        check_for_cards (bool): Check for legend stage / modifier cards

    Returns:
        None
    """
    if isinstance(image_path, Map):
        image_path = image_path.value
    r_input.PressKey("i", 1)
    ctypes.windll.user32.mouse_event(0x0001, 0, 100000, 0, 0)
    time.sleep(0.2)
    r_input.PressKey("o", 2)
    return_to_spawn()

    if image_path is not None:
        check_region = (0, 0, 399, 355) if check_region is None else check_region
        time.sleep(1.5)
        spawn_located = False
        while not spawn_located:
            while state.paused:
                time.sleep(0.1)
            if r_util.imageExists(image_path, 0.8, region=check_region):
                break
            else:
                return_to_spawn()
            time.sleep(2)
    else:
        time.sleep(2)

    if ctm_inputs is not None:
        cords = list(ctm_inputs.keys())
        delays = list(ctm_inputs.values())
        for i, cord in enumerate(cords):
            while state.paused:
                time.sleep(0.1)
            r_input.RightClick(*cord, 0.1)
            time.sleep(delays[i])

    if restart:
        start()
        time.sleep(5.5)
        restart_match()


def retry():
    """
    Click the retry button at the relative window screen position.

    Args:
        base_cord (tuple[int, int]): Screen coordinates of the retry button.

    Returns:
        None
    """
    r_input.Click(*set.retry_pixel_cords, 0.1)


def start():
    """
    Click the start button at the relative window window position.

    Args:
        None

    Returns:
        None
    """
    r_input.Click(*set.start_pixel_cord, 0.1)


def wait_for_end(check_delay=0.1):
    """
    Wait until the current match ends, then return the result.

    Args:
        check_delay (float): Delay between end-state checks in seconds.

    Returns:
        bool: True if the match ended in victory, False if it ended in defeat.
    """
    while not check_ended():
        time.sleep(check_delay)
    if check_victory():
        return True
    return False


def wait_for_spawn(check_delay=0.1):
    """
    Wait until the spawn indicator pixel matches the expected color.

    Args:
        check_delay (float): Delay between checks in seconds.

    Returns:
        None
    """
    while not r_util.pixelMatchesColor(*set.wait_for_spawn_pixel, (10, 10, 10)):
        if check_ended():
            retry()
        time.sleep(check_delay)


def check_spawned(pixel_check=(394, 123)):
    """
    Check whether the spawn indicator pixel is currently visible.

    Args:
        pixel_check (tuple[int, int]): Pixel coordinates used to detect spawn completion.

    Returns:
        bool: True if the spawn pixel matches the expected color, otherwise False.
    """
    return r_util.pixelMatchesColor(*pixel_check, (10, 10, 10))


def wait_for_color(
    pixel: tuple[int, int], color: tuple[int, int, int], tolerance: int, appear=True
):
    """
    Wait for a pixel to either match or stop matching a specific color.

    Args:
        pixel (tuple[int, int]): Screen coordinates of the pixel to monitor.
        color (tuple[int, int, int]): Expected RGB color.
        tolerance (int): Allowed color variance when comparing the pixel.
        appear (bool): If True, wait until the color appears.
            If False, wait until the color disappears.

    Returns:
        None
    """
    if appear:
        while not r_util.pixelMatchesColor(*pixel, color, tolerance):
            while state.paused:
                time.sleep(0.1)
            time.sleep(0.1)
    else:
        while r_util.pixelMatchesColor(*pixel, color, tolerance):
            while state.paused:
                time.sleep(0.1)
            time.sleep(0.1)


def lobby_path(Area: Areas, Stage: int | Stages, Act: int):
    """
    Navigate through the lobby UI to enter a selected area, stage, and act.

    Args:
        Area (Areas): Target area category to navigate to.
        Stage (int | Stages): Stage number or Stages enum value within the selected area.
            If a Stages enum is provided, its numeric value is used.
        Act (int): Act number to select for the chosen stage.

    Notes:
        - Supports multiple lobby pathing behaviors depending on the selected area.
        - For STORY mode, Act is internally incremented by 1 before selection because of sandbox.
        - Some areas use a standard stage/act selection flow, while others use custom UI flows.

    Returns:
        bool | None: False if the area icon could not be found, otherwise None.
    """

    if isinstance(Stage, Stages):
        Stage = Stage.value
    click_area = r_util.clickImage(0, 0.1, os.path.join(resources, "AreaIcon.png"), 0.8)

    if not click_area:
        print("PATH FAILURE")
        return False

    wait_for_color((765, 114), (255, 255, 255), 10)

    Area_Pos = {
        Areas.STORY: (714, 409),
        Areas.LEGEND_STAGE: (714, 409),
        Areas.RAID: (589, 406),
        Areas.DUNGEONS: (589, 406),
        Areas.CHALLENGES: (464, 408),
        Areas.BOSS_RAID: (88, 531),
        Areas.ODYSSEY: (214, 523),
        Areas.WORLDLINES: (342, 525),
        Areas.WINTER_EVENT: (589, 529),
        Areas.WHITEBEARD: (92, 258),
    }

    r_util.Click(*Area_Pos[Area], 0.1)

    Normal_Start = True

    match Area:
        case Areas.STORY | Areas.LEGEND_STAGE:
            if Area == Areas.STORY:
                Act += 1
            r_input.KeyDown("d")
            time.sleep(0.1)
            r_input.KeyDown(0x2A)
            r_input.Click(420, 327, 0.1)
            wait_for_color((139, 286), (27, 245, 60), 5)
            r_input.KeyUp("d")
            r_input.KeyUp(0x2A)
            r_input.Click(139, 286, 0.1)
            wait_for_color((39, 166), (255, 255, 255), 10)
            if Area == Areas.LEGEND_STAGE:
                r_util.Click(505, 540, 0.1)
                time.sleep(0.3)

        case Areas.RAID:
            r_input.PressKey("w", Delay=1)
            r_input.KeyDown("d")
            time.sleep(0.1)
            r_input.KeyDown(0x2A)
            r_input.Click(420, 327, 0.1)
            wait_for_color((139, 286), (27, 245, 60), 5)
            r_input.KeyUp("d")
            r_input.KeyUp(0x2A)
            r_input.Click(139, 286, 0.1)
            wait_for_color((39, 166), (255, 255, 255), 10)

        case Areas.DUNGEONS:
            r_input.PressKey("w", Delay=1)
            r_input.KeyDown("d")
            r_input.KeyDown("w")
            time.sleep(0.1)
            r_input.KeyDown(0x2A)
            r_input.Click(420, 327, 0.1)
            wait_for_color((139, 286), (27, 245, 60), 5)
            r_input.KeyUp("d")
            r_input.KeyUp("w")
            r_input.KeyUp(0x2A)
            r_input.Click(139, 286, 0.1)
            wait_for_color((39, 166), (255, 255, 255), 10)

        case Areas.CHALLENGES:
            Normal_Start = False
            r_input.PressKey("w", Delay=1.8)
            r_input.KeyDown("a")
            time.sleep(0.1)
            r_input.KeyDown(0x2A)
            r_input.Click(420, 327, 0.1)
            wait_for_color((139, 286), (27, 245, 60), 5)
            r_input.KeyUp("a")
            r_input.KeyUp(0x2A)
            r_input.Click(139, 286, 0.1)
            wait_for_color((114, 169), (255, 255, 255), 10)
            r_input.Click(220, 264 + 66 * (Stage - 1), 0.1)
            time.sleep(0.2)
            r_input.Click(497, 298, 0.1)
            time.sleep(0.2)
            scroll(-3 if Act > 3 else 0)
            r_input.Click(636, 290 + 90 * ((Act - 1) % 3) - (40 if Act > 3 else 0), 0.1)
            time.sleep(0.8)
            if r_util.imageExists(
                os.path.join(resources, "Alert.png"),
                0.8,
                region=(238, 182, 586 - 283, 471 - 182),
            ):
                r_input.Click(*(407, 366), 0.1)
                time.sleep(0.5)
            r_util.clickImage(0, 0.1, os.path.join(resources, "StartMatch.png"), 0.7)

        case Areas.BOSS_RAID:
            Normal_Start = False
            r_input.KeyDown("w")
            r_input.Click(420, 327, 0.1)
            while not r_util.pixelMatchesColor(671, 152, (255, 255, 255), 5):
                r_input.PressKey("e")
                time.sleep(0.1)
            r_input.KeyUp("e")
            r_input.Click(203, 436, 0.1)
            time.sleep(0.8)
            if r_util.imageExists(
                os.path.join(resources, "Alert.png"),
                0.8,
                region=(238, 182, 586 - 283, 471 - 182),
            ):
                r_input.Click(*(407, 366), 0.1)
                time.sleep(0.5)
            r_util.clickImage(0, 0.1, os.path.join(resources, "StartMatch.png"), 0.7)

        case Areas.ODYSSEY:
            Normal_Start = False
            r_input.KeyDown("w")
            time.sleep(0.2)
            r_input.KeyDown(0x2A)
            r_input.Click(420, 327, 0.1)
            while not r_util.pixelMatchesColor(695, 166, (255, 255, 255), 5):
                r_input.PressKey("e")
                r_input.PressKey("q")
                r_input.PressKey("q")
                time.sleep(0.1)
            r_input.KeyUp("w")
            r_input.KeyUp(0x2A)
            r_input.Click(183, 450, 0.1)
            r_input.Click(183, 450, 0.1)

        case Areas.WORLDLINES:
            Normal_Start = False
            r_input.PressKey("w", Delay=1)
            while not r_util.pixelMatchesColor(695, 166, (255, 255, 255), 5):
                r_input.PressKey("e")
                time.sleep(0.1)
            r_input.Click(*(621, 466), 0.1)
            r_input.Click(*(621, 466), 0.1)

        case Areas.WINTER_EVENT:
            Normal_Start = False
            r_input.KeyDown("s")
            time.sleep(6)
            while not r_util.pixelMatchesColor(695, 166, (255, 255, 255), 5):
                r_input.PressKey("e")
                time.sleep(0.1)
            r_input.KeyUp("s")
            r_input.Click(*(176, 473), 0.1)
            wait_for_color((464, 324), (169, 105, 236), 40)
            r_input.Click(*(354, 332), 0.1)
            wait_for_color((464, 324), (169, 105, 236), 40, appear=False)
            time.sleep(0.4)
            if r_util.imageExists(
                os.path.join(resources, "Alert.png"),
                0.8,
                region=(238, 182, 586 - 283, 471 - 182),
            ):
                r_input.Click(*(407, 366), 0.1)
                time.sleep(0.5)
            r_util.clickImage(0, 0.1, os.path.join(resources, "StartMatch.png"), 0.7)

        case Areas.WHITEBEARD:
            Normal_Start = False
            while not r_util.pixelMatchesColor(25, 604, (255, 255, 255), 20):
                time.sleep(0.1)
            r_util.RightClick(*(243, 361), 0.1)
            r_input.KeyDown(0x2A)
            while r_util.pixelMatchesColor(25, 604, (255, 255, 255), 5):
                r_input.PressKey("e")
                r_input.PressKey("q")
                r_input.PressKey("q")
                time.sleep(0.1)
            r_input.KeyUp(0x2A)
            r_input.PressKey("q")
            r_input.PressKey("q")

    if Normal_Start:
        r_util.Click(157, 233, 0.1)
        time.sleep(0.2)
        Stage_click = [150, 220 + 51 * ((Stage % 6) - 1)]
        scroll(-int((Stage - 1) / 6) * 3)
        time.sleep(0.2)
        if Stage % 6 == 0:
            Stage_click[1] = 448
        r_input.Click(*Stage_click, 0.1)
        r_input.Click(300, 220, 0.1)
        time.sleep(0.2)
        act_click = [300, 220 + 51 * ((Act % 6) - 1) + 51 * int((Act - 1) / 6) * 3]
        scroll(-int((Act - 1) / 6) * 3)
        time.sleep(0.2)
        if Act % 6 == 0:
            act_click[1] = 448
        r_input.Click(*act_click, 0.1)
        time.sleep(0.1)
        r_input.Click(*(442, 479), 0.1)
        time.sleep(0.8)
        if r_util.imageExists(
            os.path.join(resources, "Alert.png"),
            0.8,
            region=(238, 182, 586 - 283, 471 - 182),
        ):
            r_input.Click(*(407, 366), 0.1)
            time.sleep(0.5)
        r_util.clickImage(0, 0.1, os.path.join(resources, "StartMatch.png"), 0.7)


def read_wave(wave_images: str | None = None) -> int:
    """
    Read the current wave number from the Roblox UI using template matching.

    Args:
        wave_images (str | None): Directory containing wave number template images.
            Defaults to the local resources/WaveNumbers folder.

    Returns:
        int: The detected wave number, or -1 if no digits were found or parsing failed.

    Notes:
        - Wave digit templates are cached after the first load in cached_wave_numbers.
        - The function captures the configured wave number screen region relative to the Roblox window.
        - Template matching uses a threshold of 0.89 after binary inversion.
    """
    global cached_wave_numbers

    wave_images = (
        os.path.join(resources, "WaveNumbers") if wave_images is None else wave_images
    )
    if cached_wave_numbers.get(1) is None:
        for i, photo in enumerate(os.listdir(wave_images)):
            cached_wave_numbers[i + 1] = cv2.imread(wave_images + "\\" + photo)
            _, cached_wave_numbers[i + 1] = cv2.threshold(
                cached_wave_numbers[i + 1], 250, 255, cv2.THRESH_BINARY_INV
            )
    roblox_position = get_geometry(get_roblox_hwnd())
    roblox_position = (roblox_position.x, roblox_position.y)
    wave = []
    img_cv2 = r_util.captureRegion(
        (
            set.wave_number_region[0] + roblox_position[0],
            set.wave_number_region[1] + roblox_position[1],
            set.wave_number_region[2] + roblox_position[0],
            set.wave_number_region[3] + roblox_position[1],
        )
    )
    _, img_cv2 = cv2.threshold(img_cv2, 250, 255, cv2.THRESH_BINARY_INV)
    for i in range(10):
        template = cached_wave_numbers[i + 1]
        res = cv2.matchTemplate(img_cv2, template, cv2.TM_CCOEFF_NORMED)
        loc = numpy.where(res >= 0.89)
        for pt in zip(*loc[::-1]):
            wave.append([pt[0], i])
    if len(wave) == 0:
        return -1
    wave_number = ""
    while wave != []:
        leftmost = min(wave)
        wave_number += str(leftmost[1])
        wave.remove(leftmost)
    try:
        return int(wave_number)
    except Exception:
        return -1


def return_to_spawn(mouse_cords=None) -> None:
    """
    Return the player to spawn by clicking a sequence of UI positions.

    Args:
        mouse_cords (list[tuple[int, int]] | None): Sequence of click positions used to return to spawn.
            Defaults to the built-in spawn return click path.

    Returns:
        None
    """
    mouse_cords = (
        [(29, 606), (704, 320), (756, 151)] if mouse_cords is None else mouse_cords
    )
    for pos in mouse_cords:
        r_input.Click(*pos, 0.1)
        if pos == (29, 606):
            while not r_util.pixelMatchesColor(754, 152, (255, 255, 255), 40):
                time.sleep(0.1)
        else:
            time.sleep(0.2)


def cards_exist() -> bool:
    """
    Check whether any card selection UI is currently visible.

    Args:
    None

    Returns:
    bool: True if any known card UI (dungeon, stage modifier, or starter cards) is detected, otherwise False.
    """
    card_path_dungeon = os.path.join(resources, "DungeonCardExist.png")
    card_path_stage = os.path.join(resources, "ModifiersExist.png")
    card_path_starter = os.path.join(resources, "StarterCards.png")
    if (
        r_util.imageExists(card_path_dungeon, 0.7, region=set.card_check_region)
        or r_util.imageExists(card_path_stage, 0.7, region=set.card_check_region)
        or r_util.imageExists(card_path_starter, 0.7, region=set.card_check_region)
    ):
        return True
    return False


def starter_card_selector(card: Card | str, legend_stage=True):
    """
    Select a starter or legend-stage card by name.

    Args:
    card (Card | str): Card enum or string name of the card to select.
    legend_stage (bool): Whether the selection is for a legend stage (different cards).

    Returns:
    None
    """
    if isinstance(card, Card):
        card = card.value
    if legend_stage:
        card_path = os.path.join(resources, "LegendStage", card + ".png")
        r_util.Click(535, 315, 0.1)
        time.sleep(0.5)
        scroll(-10)
        time.sleep(0.5)
        if r_util.imageExists(card_path, 0.8, region=set.card_region):
            loc = r_util.imageLocation(card_path, 0.8, region=set.card_region)
            r_util.Click(loc.x + set.card_region[0], loc.y + set.card_region[1], 0.1)
            return
        scroll(10)
        time.sleep(0.5)
        if r_util.imageExists(card_path, 0.8, region=set.card_region):
            loc = r_util.imageLocation(card_path, 0.8, region=set.card_region)
            r_util.Click(loc.x + set.card_region[0], loc.y + set.card_region[1], 0.1)
            return
    else:
        card_selected = False
        while not card_selected:
            card_path = os.path.join(resources, "DungeonCards", card + ".png")
            if r_util.imageExists(card_path, 0.8, region=set.card_region):
                loc = r_util.imageLocation(card_path, 0.8, region=set.card_region)
                r_util.Click(
                    loc.x + set.card_region[0], loc.y + set.card_region[1], 0.1
                )
                card_selected = True
                return
            else:
                start()
                r_util.Click(406, 302, 0.1)
                r_util.Click(406, 302, 0.1)
                time.sleep(5.5)
                restart_match()
                time.sleep(2)


def card_selector(priority: list[Card] | List[str]) -> bool:
    """
    Select a card based on a priority list.

    Args:
    priority (list[Card] | list[str]): Ordered list of cards to attempt selecting.

    Returns:
    bool: True if a card was successfully selected, otherwise False.
    """
    if any(isinstance(arg, Card) for arg in priority):
        priority = [arg.value if isinstance(arg, Card) else arg for arg in priority]
    card_priority = priority
    card_path = os.path.join(resources, "DungeonCards")
    for card in card_priority:
        current_card = os.path.join(card_path, card + ".png")
        if r_util.imageExists(current_card, 0.8, region=set.card_region):
            try:
                loc = r_util.imageLocation(current_card, 0.8, region=set.card_region)
                r_util.Click(
                    loc.x + set.card_region[0], loc.y + set.card_region[1], 0.1
                )
                return True
            except Exception as e:
                print(f"Error in card selector {e}")
    return False


def restart_match():
    """
    Restart the current match by clicking through the restart UI flow.

    Args:
        None

    Returns:
        None
    """
    mouse_cords = [(28, 606), (704, 290), (346, 365), (406, 369), (757, 156)]
    for pos in mouse_cords:
        if pos == (406, 369):
            while not r_util.pixelMatchesColor(407, 293, (98, 98, 98), 20):
                time.sleep(0.1)
            r_input.Click(*pos, 0.1)
        else:
            r_input.Click(*pos, 0.1)
            time.sleep(0.2)
