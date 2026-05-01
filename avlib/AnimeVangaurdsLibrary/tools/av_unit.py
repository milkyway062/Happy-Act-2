import ctypes
import time

from rblib import r_input, r_util

from AnimeVangaurdsLibrary import Game_Settings as GS

from .av_game import check_ended
from .state import get_state

global set, state
state = get_state()
set = GS.avus


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


def place_unit(
    hotbar_index: int,
    unit_position: tuple[int, int],
    auto_upgrade=False,
    close_unit=False,
    is_uma=False,
) -> bool:
    """
    Place a unit from the hotbar at the specified position.

    Args:
        hotbar_index (int): Hotbar slot number of the unit to place.
        unit_position (tuple[int, int]): Roblox window coordinates where the unit should be placed.
        auto_upgrade (bool): Whether to automatically enable auto-upgrade after placing the unit.
        close_unit (bool): Whether to close the unit menu after placement.
        is_uma (bool): If the unit is horsegirls racing, this requires special placement which picks the type based off of AVUS.

    Returns:
        bool: True if the unit was successfully placed, False if the game ended before placement completed.
    """
    r_input.PressKey(f"{hotbar_index}")
    r_input.Click(*unit_position, set.unit_place_click_delay)

    placement_begin = time.time() + set.unit_place_timeout
    while not r_util.pixelMatchesColor(
        *set.unit_place_close_check, (255, 255, 255)
    ) and not r_util.pixelMatchesColor(
        *set.unit_place_close_check_two, (107, 166, 223), 10
    ):
        if is_uma:
            if r_util.pixelMatchesColor(418, 150, (193, 73, 255), 10):
                match set.horsegirl_unit.lower():
                    case "speed":
                        r_input.Click(171, 450, 0.1)
                    case "damage":
                        r_input.Click(331, 450, 0.1)
                    case "crit":
                        r_input.Click(483, 450, 0.1)
                    case "cost":
                        r_input.Click(636, 450, 0.1)
                break
        if check_ended():
            print("match_ended")
            return False
        while state.paused:
            time.sleep(0.1)
        if time.time() - placement_begin >= 0:
            r_input.PressKey("q")
            r_input.PressKey(f"{hotbar_index}")
            r_input.Click(*unit_position, set.unit_place_click_delay)
            placement_begin = time.time() + set.unit_place_timeout
            print("timeout")
            time.sleep(set.unit_place_check_delay)
        time.sleep(set.unit_place_check_delay)
    print(
        f"Placed unit: {r_util.pixel(*set.unit_place_close_check), r_util.pixel(*set.unit_place_close_check_two)}"
    )
    if auto_upgrade:
        r_input.PressKey("z")
    if close_unit:
        r_input.Click(*set.unit_place_close_check, 0.1)

    return True


def close_unit():
    """
    Close the currently opened unit menu.

    Args:
        None

    Returns:
        None
    """
    r_input.Click(*set.unit_place_close_check, 0.1)


def place_with_image(
    image_path: str,
    unit_position: tuple[int, int],
    auto_upgrade=False,
    close_unit=False,
):
    """
    Locate a unit in the unit list by image and place it at the specified position.

    Args:
        image_path (str): Path to the reference image used to find the unit.
        unit_position (tuple[int, int]): Roblox window coordinates where the unit should be placed.
        auto_upgrade (bool): Whether to automatically enable auto-upgrade after placing the unit.
        close_unit (bool): Whether to close the unit menu after placement.

    Returns:
        bool: True if the unit was successfully placed, False if the game ended before placement completed.
    """

    unit_location = r_util.imageLocation(
        path=image_path,
        confidence=set.unit_place_image_confidence,
        grayscale=set.unit_place_image_grayscale,
        region=set.unit_place_image_region,
    )
    while not unit_location:
        if check_ended():
            return False
        while state.paused:
            time.sleep(0.1)
        unit_location = r_util.imageLocation(
            path=image_path,
            confidence=set.unit_place_image_confidence,
            grayscale=set.unit_place_image_grayscale,
            region=set.unit_place_image_region,
        )
        time.sleep(set.unit_place_check_delay)
    r_input.Click(
        unit_location.x + set.unit_place_image_region[0],
        unit_location.y + set.unit_place_image_region[1],
        0.1,
    )
    r_input.Click(*unit_position, set.unit_place_click_delay)

    placement_begin = time.time() + set.unit_place_timeout
    while not r_util.pixelMatchesColor(
        *set.unit_place_close_check, (255, 255, 255)
    ) and not r_util.pixelMatchesColor(
        *set.unit_place_close_check_two, (107, 166, 223), 10
    ):
        if check_ended():
            return False
        while state.paused:
            time.sleep(0.1)
        if time.time() - placement_begin >= 0:
            r_input.Click(
                unit_location.x + set.unit_place_image_region[0],
                unit_location.y + set.unit_place_image_region[1],
                0.1,
            )
            r_input.Click(*unit_position, set.unit_place_click_delay)
            placement_begin = time.time() + set.unit_place_timeout
            print("timeout")
            time.sleep(set.unit_place_check_delay)
        time.sleep(set.unit_place_check_delay)
    if auto_upgrade:
        r_input.PressKey("z")
    if close_unit:
        r_input.Click(*set.unit_place_close_check, 0.1)
    return True


def select_unit(unit_position: tuple[int, int], stop_if_opened=False):
    """
    Select a placed unit by clicking its position until the unit menu opens.

    Args:
        unit_position (tuple[int, int]): Screen coordinates of the unit to select.
        stop_if_opened (bool): Whether to immediately return if the unit menu is already open.

    Returns:
        bool: True if the unit was successfully selected, False if the game ended before selection completed.
    """
    if (
        stop_if_opened
        and not r_util.pixelMatchesColor(*set.unit_place_close_check, (255, 255, 255))
        and not r_util.pixelMatchesColor(
            *set.unit_place_close_check_two, (107, 166, 223), 10
        )
    ):
        return True

    r_input.Click(*unit_position, set.unit_place_click_delay)

    placement_begin = time.time() + set.unit_place_timeout
    while not r_util.pixelMatchesColor(
        *set.unit_place_close_check, (255, 255, 255)
    ) and not r_util.pixelMatchesColor(
        *set.unit_place_close_check_two, (107, 166, 223), 10
    ):
        if check_ended():
            return False
        while state.paused:
            time.sleep(0.1)
        if time.time() - placement_begin >= 0:
            r_input.Click(*unit_position, set.unit_place_click_delay)
            placement_begin = time.time() + set.unit_place_timeout
            print("timeout")
            time.sleep(set.unit_place_check_delay)
        time.sleep(set.unit_place_check_delay)
    return True


def sell_unit(unit_position: tuple[int, int], stop_if_opened=False):
    """
    Select a unit and repeatedly attempt to sell it until the unit menu closes.

    Args:
        unit_position (tuple[int, int]): Screen coordinates of the unit to sell.
        stop_if_opened (bool): Whether to skip reselecting the unit if the unit menu is already open.

    Returns:
        bool: False if the game ended before the unit was sold, otherwise None.
    """
    select_unit(unit_position, stop_if_opened)

    r_input.PressKey("x")
    r_input.PressKey("x")
    sell_begin = time.time() + set.unit_place_timeout
    while r_util.pixelMatchesColor(
        *set.unit_place_close_check, (255, 255, 255)
    ) and r_util.pixelMatchesColor(
        *set.unit_place_close_check_two, (107, 166, 223), 10
    ):
        if check_ended():
            return False
        while state.paused:
            time.sleep(0.1)
        if time.time() - sell_begin >= 0:
            r_input.PressKey("x")
            sell_begin = time.time() + set.unit_place_timeout
            print("timeout")
            time.sleep(set.unit_place_check_delay)
        time.sleep(set.unit_place_check_delay)


def use_team(number: int):
    """
    Open the team selection menu and switch to the specified team slot.

    Args:
        number (int): Team number to switch to.

    Returns:
        None
    """
    c_m1 = (643, 189)  # unit menu
    c_m2 = (660, 196)  # team menu
    c_ta = (406, 357)  # close team alert

    change_lineup = (410, 499)
    teams = (406, 230)
    team_alert = (432, 295)
    focus = (405, 291)

    ct_alert = (20, 20, 32)

    r_util.Click(*change_lineup, 0.1)
    while not r_util.pixelMatchesColor(*c_m1, (255, 255, 255), 10):
        time.sleep(0.1)
    r_util.Click(*teams, 0.1)
    while not r_util.pixelMatchesColor(*c_m2, (247, 247, 247), 10):
        time.sleep(0.1)
    r_util.Click(*focus, 0.1)
    scroll(-2)
    base_team = [350, 375]
    dy = 18
    num_scroll = (number - 1) * -4
    print(num_scroll)
    base_team[1] -= int(num_scroll / 8 * -1 * dy)
    if number == 12:
        scroll(-44)
        r_input.Click(*(349, 429), 0.1)
        r_input.Click(*(349, 429), 0.1)
    else:
        scroll(num_scroll)
        print(base_team)
        r_input.Click(*base_team, 0.1)
        r_input.Click(*base_team, 0.1)
    while not r_util.pixelMatchesColor(*team_alert, ct_alert, 5):
        time.sleep(0.1)
    r_util.Click(*c_ta, 0.1)
    while not r_util.pixelMatchesColor(*c_m2, (247, 247, 247), 10):
        time.sleep(0.1)
    r_util.Click(*c_m2, 0.1)
    while not r_util.pixelMatchesColor(*c_m1, (255, 255, 255), 10):
        time.sleep(0.1)
    r_util.Click(*c_m1, 0.1)
