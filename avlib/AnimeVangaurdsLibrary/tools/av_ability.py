import ctypes
import os
import time
from threading import Event

from rblib import r_input, r_util

from AnimeVangaurdsLibrary import Game_Settings as GS

from .av_game import read_wave
from .state import get_state

global set, state
state = get_state()
set = GS.avas

resources = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")


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


def _no_exit_place_unit(
    unit_position: tuple[int, int], auto_upgrade=False, close_unit=False
) -> bool:
    """
    Internal function to place units without cancel

    Args:
        unit_position (tuple[int, int]): Roblox window coordinates where the unit should be placed.
        auto_upgrade (bool): Whether to automatically enable auto-upgrade after placing the unit.
        close_unit (bool): Whether to close the unit menu after placement.

    Returns:
        bool: True when the unit is successfully placed.
    """

    r_input.Click(*unit_position, set.unit_place_click_delay)

    placement_begin = time.time() + set.unit_place_timeout
    while not r_util.pixelMatchesColor(*set.unit_place_close_check, (255, 255, 255)):
        while state.paused:
            time.sleep(0.1)
        if time.time() - placement_begin >= 0:
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


def brook_buff(stop_event: Event | None = None):
    """
    Activate Brook's rhythm ability and spam ["a", "s", "d", "f", "g"] untill it has been 10 seconds or event is set.

    Args:
        stop_event (Event | None): Optional threading event used to stop the buff loop early.

    Returns:
        None
    """
    print(f"Recieved {stop_event}")
    base_ability()
    brook = False
    keys = ["a", "s", "d", "f", "g"]
    auto_end = time.time() + 10
    while not brook:
        while state.paused:
            time.sleep(0.1)
        # If the Brook prompt is visible (white pixel), the rhythm window is active
        if time.time() - auto_end > 0:
            print("timeout")
            break
        if stop_event is not None and stop_event.is_set():
            print("stop event was set")
            break
        if r_util.pixelMatchesColor(*set.brook_ability_close, (255, 255, 255)):
            for k in keys:
                r_input.KeyUp(k)

            for k in keys:
                r_input.KeyDown(k)

            time.sleep(0.02)
            for k in keys:
                r_input.KeyUp(k)
        else:
            # If the prompt isn't visible yet, keep trying to activate ability 1
            base_ability()
            time.sleep(0.5)
    print("Exited brook")
    # Close Brook's ability UI when done
    while r_util.pixelMatchesColor(*set.brook_ability_close, (255, 255, 255)):
        r_util.Click(*set.brook_ability_close, 0.1)
        time.sleep(0.2)


def base_ability(auto=False):
    """
    Use the unit's first ability button.

    Args:
        auto (bool): Whether to click the auto-cast version of the first ability button.

    Returns:
        None
    """
    r_input.Click(*set.unit_ability_one, delay=0.1) if not auto else r_input.Click(
        *set.unit_ability_one_auto, delay=0.1
    )


def second_ability(auto=False):
    """
    Use the unit's second ability button.

    Args:
        auto (bool): Whether to click the auto-cast version of the second ability button.

    Returns:
        None
    """
    r_input.Click(*set.unit_ability_two, delay=0.1) if not auto else r_input.Click(
        *set.unit_ability_two_auto, delay=0.1
    )


def third_ability():
    """
    Use the unit's third ability button.

    Args:
        None

    Returns:
        None
    """
    r_input.Click(*set.unit_ability_three, delay=0.1)


def prideburn(slotnumber: int):
    """
    Activate Prideburn ability while disabling all other unit slots except the specified one.

    Args:
        slotnumber (int): The slot index (1–6) to keep active.

    Returns:
        None
    """
    prideburn_button = (409, 445)
    slots = [(237, 569), (308, 572), (374, 572), (445, 574), (511, 573), (579, 573)]
    r_util.Click(*prideburn_button, 0.1)
    time.sleep(0.5)
    for index, pos in enumerate(slots):
        if index + 1 != slotnumber:
            r_util.Click(*pos, 0.1)
    r_util.Click(*prideburn_button, 0.1)


def vsjw(nuke: int | None = None, shadows: dict | None = None):
    """
    Execute VSJW abilities including optional nuke selection and shadow summoning.

    Args:
        nuke (int | None): Index (1–3) of the nuke ability to use. If None, no nuke is used.
        shadows (dict | None): Mapping of shadow types to their slot indices.
            Supported keys:
                - "arise"
                - "bear"
                - "steel"
                - "healer"
                - "belu"

    Returns:
        str | None: "No unit" if unit UI is not open, otherwise None.
    """
    if not r_util.pixelMatchesColor(
        *GS.avus.unit_place_close_check, (255, 255, 255), 10
    ):
        return "No unit"

    base_ability()
    shadow_button = (378, 283)
    nuke_button = (424, 286)

    vsjw_nukes = [(403, 327), (444, 325), (404, 365)]
    arise = (210, 455)
    bear = [(442, 240), (468, 239), (497, 239), (523, 239)]
    steel = [(106, 240), (134, 239), (161, 239), (188, 239)]
    healer = [(369, 239), (398, 239), (427, 238), (454, 240)]
    belu = [(635, 238), (663, 240), (692, 241), (719, 242)]
    if nuke is not None:
        time.sleep(0.8)
        r_util.Click(*nuke_button, 0.1)
        time.sleep(0.8)
        r_util.Click(*vsjw_nukes[nuke - 1], 0.1)
        time.sleep(0.8)
        if r_util.pixelMatchesColor(407, 297, (50, 50, 50)) or r_util.pixelMatchesColor(
            414, 285, (106, 106, 106)
        ):
            r_util.Click(405, 359, 0.1)
        r_util.Click(*nuke_button, 0.1)
        if shadows is None:
            base_ability()
    if shadows is not None:
        if nuke is not None:
            base_ability()
        time.sleep(0.8)
        r_util.Click(*shadow_button, 0.1)
        while not r_util.pixelMatchesColor(718, 166, (245, 245, 245), 10):
            time.sleep(0.1)
        scroll(-6)
        for key in list(shadows.keys()):
            match key.lower():
                case "arise":
                    scroll(10)
                    r_util.Click(*arise, 0.1)
                    scroll(-6)
                case "bear":
                    scroll(10)
                    r_util.Click(*bear[shadows[key] - 1], 0.1)
                    scroll(-6)
                case "steel":
                    r_util.Click(*steel[shadows[key] - 1], 0.1)
                case "healer":
                    r_util.Click(*healer[shadows[key] - 1], 0.1)
                case "belu":
                    print("belu")
                    r_util.Click(*belu[shadows[key] - 1], 0.1)
        r_util.Click(718, 166, 0.1)
        base_ability()


def armored_mage(buff: int):
    """
    Activate Armored Mage ability and select a buff option.

    Args:
        buff (int): Multiplier index used to determine which buff option to select.

    Returns:
        str | None: "Unit not opened" if unit UI is not available, otherwise None.
    """
    if r_util.pixelMatchesColor(*GS.avus.unit_place_close_check, (255, 255, 255), 10):
        base_ability()
        while not r_util.pixelMatchesColor(694, 165, (255, 255, 255), 10):
            time.sleep(0.1)
        while not r_util.pixelMatchesColor(405, 326, (255, 255, 255), 25):
            r_util.Click(200 * buff, 460, 0.1)
            time.sleep(0.2)
        r_util.Click(400, 358, 0.1)
        r_util.Click(400, 358, 0.1)
        r_util.Click(694, 165, 0.1)
    else:
        return "Unit not opened"


def uma_racing():
    """
    Automate Uma Racing upgrade system by prioritizing upgrades based on mood and availability.

    Args:
        None

    Returns:
        None
    """
    if not r_util.pixelMatchesColor(
        *GS.avus.unit_place_close_check, (255, 255, 255), 10
    ):
        return "No unit"
    speed = (368, 309)
    damage = (520, 309)
    crit = (524, 391)
    cost = (365, 394)
    rest = (281, 421)
    upg_region_speed = (280, 230, 52, 96)
    upg_region_damage = (442, 288, 45, 41)
    upg_region_cost = (285, 362, 47, 46)
    upg_region_crit = (444, 364, 41, 46)
    menu_region = (252, 218, 315, 223)
    uma_upgrades = [False, False, False, False]
    base_ability()
    while not r_util.pixelMatchesColor(561, 227, (255, 255, 255), 10):
        time.sleep(0.1)
    actions = 4
    last_wave = read_wave()
    print("Starting upgrading")
    while not all(uma_upgrades):
        while actions > 0:
            if all(uma_upgrades):
                break
            print(actions)
            time.sleep(0.8)
            if r_util.imageExists(
                path=os.path.join(resources, "Alert.png"),
                confidence=0.9,
                region=menu_region,
            ):
                r_util.Click(406, 368, 0.1)
                time.sleep(0.5)
            if r_util.imageExists(
                path=os.path.join(resources, "Uma", "GreatMood.png"),
                confidence=0.9,
                region=(250, 218, 160, 40),
            ):
                print("is great mood")
                if not uma_upgrades[0] and actions > 0:
                    print(uma_upgrades[0])
                    if not r_util.imageExists(
                        path=os.path.join(resources, "Uma", "Uma_Max.png"),
                        confidence=0.99,
                        region=upg_region_speed,
                    ):
                        r_util.Click(*speed, 0.1)
                        actions -= 1
                    else:
                        print("speed done")
                        uma_upgrades[0] = True

                if not uma_upgrades[1] and actions > 0:
                    if not r_util.imageExists(
                        path=os.path.join(resources, "Uma", "Uma_Max.png"),
                        confidence=0.99,
                        region=upg_region_damage,
                    ):
                        r_util.Click(*damage, 0.1)
                        actions -= 1
                    else:
                        print("damage done")
                        uma_upgrades[1] = True
                if uma_upgrades[3] and not uma_upgrades[2] and actions > 0:
                    if not r_util.imageExists(
                        path=os.path.join(resources, "Uma", "Uma_Max.png"),
                        confidence=0.99,
                        region=upg_region_cost,
                    ):
                        r_util.Click(*cost, 0.1)
                        actions -= 1
                    else:
                        print("cost done")
                        uma_upgrades[2] = True
                if not uma_upgrades[3] and actions > 0:
                    if not r_util.imageExists(
                        path=os.path.join(resources, "Uma", "Uma_Max.png"),
                        confidence=0.99,
                        region=upg_region_crit,
                    ):
                        print("crit")
                        r_util.Click(*crit, 0.1)
                        actions -= 1
                    else:
                        print("crit done")
                        uma_upgrades[3] = True
            else:
                if actions > 0:
                    print("rest")
                    r_util.Click(*rest, 0.1)
                    actions -= 1
                    time.sleep(0.8)

        if all(uma_upgrades):
            break
        while (wave := read_wave()) == last_wave or wave == -1:
            if r_util.imageExists(
                path=os.path.join(resources, "Alert.png"),
                confidence=0.9,
                region=menu_region,
            ):
                r_util.Click(406, 368, 0.1)
            time.sleep(0.5)

        last_wave = wave
        print(last_wave)
        actions = 4
    r_util.Click(561, 227, 0.1)


def law(zone: int):
    """
    Activate Law ability and select a zone.

    Args:
        zone (int): Zone index used to determine which area to target.

    Returns:
        str | None: "Unit not opened" if unit UI is not available, otherwise None.
    """
    if r_util.pixelMatchesColor(*GS.avus.unit_place_close_check, (255, 255, 255), 10):
        base_ability()
        while not r_util.pixelMatchesColor(694, 165, (255, 255, 255), 10):
            time.sleep(0.1)

        r_util.Click(200 * zone, 460, 0.1)

        r_util.Click(694, 165, 0.1)
    else:
        return "Unit not opened"


def valentine_clones(clone_pos: list):
    """
    Spawn Valentine clones at specified positions.

    Args:
        clone_pos (list[tuple[int, int]]): List of positions where clones will be placed.

    Returns:
        str | None: "No unit" if unit UI is not open, otherwise None.
    """
    if not r_util.pixelMatchesColor(
        *GS.avus.unit_place_close_check, (255, 255, 255), 10
    ):
        return "No unit"
    base_ability()
    r_input.KeyDown(0x2A)
    for i in clone_pos:
        r_util.Click(*i, 0.01)
        time.sleep(0.3)
    r_input.KeyUp(0x2A)


def dio_reality_overwrite(effect: str):
    """
    Apply a specific status effect using Dio's Reality Overwrite ability.

    Args:
        effect (str): Name of the effect to apply (not case sensitive).
            Supported values:
                - "STUN", "BURN", "SCORCHED", "BUBLED",
                - "BLEED", "RUPTURE", "SLOW", "FREEZE", "WOUNDED"

    Returns:
        str | None: "No unit" if unit UI is not open, otherwise None.
    """
    if not r_util.pixelMatchesColor(
        *GS.avus.unit_place_close_check, (255, 255, 255), 10
    ):
        return "No unit"
    c = 0
    r = 0
    base_ability()
    while not r_util.pixelMatchesColor(667, 183, (255, 255, 255), 10):
        print(r_util.pixel(655, 183))
        time.sleep(0.1)
    match effect.upper():
        case "STUN":
            c, r = 1, 2
        case "BURN":
            c, r = 0, 0
        case "SCORCHED":
            c, r = 0, 1
        case "BUBLED":
            c, r = 0, 2
        case "BLEED":
            c, r = 1, 0
        case "RUPTURE":
            c, r = 1, 1
        case "SLOW":
            c, r = 2, 0
        case "FREEZE":
            c, r = 2, 1
        case "WOUNDED":
            c, r = 2, 2
        case _:
            return  # or raise error

    r_input.Click(250 + (r * 175), 291 + (c * 78), delay=0.1)
    r_input.Click(666, 182, delay=0.1)


def ichigo_nuke(stocks: int):
    if not r_util.pixelMatchesColor(
        *GS.avus.unit_place_close_check, (255, 255, 255), 10
    ):
        return "No unit"
    base_ability()
    while not r_util.pixelMatchesColor(613, 271, (255, 255, 255), 10):
        time.sleep(0.1)
    r_util.Click(279 + 120 * (stocks - 1), 336, 0.1)
    r_util.Click(*(411, 402), 0.1)


def ainz_abiliy(Ability: str, Args: tuple):
    """
    Execute Ainz's special abilities based on the provided ability type and arguments.

    Args:
        Ability (str): The ability category to use.
            Supported values:
            - "spells": Opens the spell menu and selects one or more spells.
            - "worlditem": Opens the world item menu and uses a specific world item action.

        Args (tuple): Arguments required for the selected ability type.

            For Ability == "spells":
                Args should be a tuple of spell tokens.
                Each token is a string in the format:
                    "<spell_code><slot_numbers>"
                Example:
                    ("fi1", "pa12")

                Spell codes:
                    - "bl" = Blast
                    - "co" = Cosmic
                    - "cu" = Curse
                    - "el" = Elementless
                    - "fi" = Fire
                    - "ho" = Holy
                    - "na" = Nature
                    - "pa" = Passion
                    - "sp" = Spark
                    - "un" = Unbound
                    - "wa" = Water

                Slot numbers:
                    - "1" = Select the first option for that spell
                    - "2" = Select the second option for that spell
                    A token may include one or both, such as "pa12".

            For Ability == "worlditem":
                Args[0] should be the world item code.

                Supported world item codes:
                    - "ws"
                    - "bom"
                    - "cs"
                    - "soman"
                    - "11eo"
                    - "o"

                Per world item:

                "ws":
                    Args = ("ws",)
                    Uses the world savior world item

                "bom":
                    Args = ("bom",)
                    Uses the branch of mielikki world item

                "cs":
                    Args = ("cs", search_text, place_position, *flags)
                    - search_text (str): Text typed into the search box.
                    - place_position (tuple[int, int]): Position passed to _no_exit_place_unit().
                    - flags (optional): Additional strings such as "auto" and/or "close".
                        - "auto": Enable auto-upgrade after placement
                        - "close": Close the unit menu after placement

                    Example:
                        ("cs", "alocard", (500, 300), "auto", "close")

                "soman":
                    Args = ("soman", first_click, second_click)
                    - first_click (tuple[int, int]): First target click position.
                    - second_click (tuple[int, int]): Second target click position.

                "11eo":
                    Args = ("11eo",)
                    Uses the 11 elements overcoming world item

                "o":
                    Args = ("o", stat_type, value)
                    - stat_type (str): Which stat condition to set.
                        Supported values:
                        - "hp"
                        - "wave"
                        - "cost"
                    - value (str): Text entered into the value field.

                    Example:
                        ("o", "wave", "1")

    Returns:
        str | None: An error message if the ability or world item is not recognized, otherwise None.
    """
    print(Ability, Args)
    tokens = Args
    spells = {
        "bl": os.path.join(resources, "Ainz", "Blast.png"),
        "co": os.path.join(resources, "Ainz", "Cosmic.png"),
        "cu": os.path.join(resources, "Ainz", "Curse.png"),
        "el": os.path.join(resources, "Ainz", "Elementless.png"),
        "fi": os.path.join(resources, "Ainz", "Fire.png"),
        "ho": os.path.join(resources, "Ainz", "Holy.png"),
        "na": os.path.join(resources, "Ainz", "Nature.png"),
        "pa": os.path.join(resources, "Ainz", "Passion.png"),
        "sp": os.path.join(resources, "Ainz", "Spark.png"),
        "un": os.path.join(resources, "Ainz", "Unbound.png"),
        "wa": os.path.join(resources, "Ainz", "Water.png"),
    }
    spells_back = (228, 248)
    spells_confirm = (568, 433)
    match Ability.lower():
        case "spells":
            time.sleep(0.5)
            second_ability()
            time.sleep(0.3)
            while not r_util.pixelMatchesColor(609, 216, (255, 255, 255), 10):
                time.sleep(0.1)
            for token in tokens[0:]:
                print(token)
                if spell_path := spells.get(token[:2].lower()):
                    while r_util.pixelMatchesColor(*(218, 247), (210, 0, 73), 50):
                        time.sleep(0.1)
                    time.sleep(0.3)
                    r_util.clickImage(
                        path=spell_path,
                        click=0,
                        delay=0.1,
                        confidence=0.7,
                    )
                    for num in token[2:]:
                        if num == "1":
                            r_input.Click(429, 278, delay=0.1)
                        elif num == "2":
                            second_offset = 317
                            if spell_path == spells["pa"]:
                                second_offset += 20
                            r_input.Click(429, second_offset, delay=0.1)
                    r_input.Click(*spells_back, 0.1)
            r_input.Click(*spells_confirm, 0.1)
        case "worlditem":
            time.sleep(0.5)
            third_ability()
            time.sleep(0.3)
            while not r_util.pixelMatchesColor(667, 182, (255, 255, 255), 10):
                time.sleep(0.1)
            world_items = ["ws", "bom", "cs", "soman", "11eo", "o"]
            base_click = [358, 274]
            dy = 87
            dx = 260
            if tokens[0] in world_items:
                ind = world_items.index(tokens[0])
                ax = 1 if ind > 2 else 0
                ind %= 3
                base_click[0] += ax * dx
                base_click[1] += ind * dy
                r_input.Click(*base_click, 0.1)
            else:
                return "World item not recognized"

            match tokens[0]:
                case "ws":
                    time.sleep(1)
                    r_util.Click(*(410, 366), 0.1)
                    r_util.Click(*(666, 184), 0.1)

                case "bom":
                    time.sleep(1)
                    r_util.Click(*(410, 366), 0.1)
                    r_util.Click(*(666, 184), 0.1)
                case "cs":
                    while not r_util.pixelMatchesColor(667, 182, (255, 255, 255), 10):
                        time.sleep(0.1)
                    search = (216, 234)
                    time.sleep(1)
                    r_util.Click(*search, 0.1)
                    r_util.Click(*search, 0.1)
                    time.sleep(0.2)
                    for c in tokens[1]:
                        r_input.KeyDown(c)
                    for c in tokens[1]:
                        r_input.KeyUp(c)
                    time.sleep(0.5)
                    r_input.Click(216, 286, 0.1)
                    time.sleep(0.4)
                    r_input.Click(316, 336, 0.1)
                    auto = True if "auto" in tokens else False
                    close = True if "close" in tokens else False
                    _no_exit_place_unit(tokens[2], auto, close)
                case "soman":
                    time.sleep(1)
                    r_input.Click(*tokens[1], 0.1)
                    time.sleep(1)
                    r_input.Click(*tokens[2], 0.1)
                case "11eo":
                    time.sleep(1)
                    r_input.Click(*(410, 366), 0.1)
                    r_input.Click(*(666, 184), 0.1)
                case "o":
                    type_box = (407, 286)
                    time.sleep(1)
                    r_input.Click(*type_box, 0.1)
                    r_input.Click(*type_box, 0.1)
                    for char in tokens[2]:
                        r_input.KeyDown(char)
                    time.sleep(0.1)
                    for char in tokens[2]:
                        r_input.KeyUp(char)
                    match tokens[1]:
                        case "hp":
                            r_input.Click(408, 344, 0.1)
                        case "wave":
                            r_input.Click(411, 386, 0.1)
                        case "cost":
                            r_input.Click(412, 428, 0.1)
                    time.sleep(1)
                    r_util.Click(*(410, 366), 0.1)
                    r_util.Click(*(666, 184), 0.1)
        case _:
            return "Ainz ability not recognized"
