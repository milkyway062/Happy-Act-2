import json
import os


class av_ability_settings:
    def __init__(
        self,
        unit_ability_one: tuple[int, int],
        unit_ability_one_auto: tuple[int, int],
        unit_ability_two: tuple[int, int],
        unit_ability_two_auto: tuple[int, int],
        unit_ability_three: tuple[int, int],
        unit_place_close_check: tuple[int, int],
        unit_place_check_delay: float,
        unit_place_timeout: float,
        unit_place_click_delay: float,
        brook_ability_close: tuple[int, int],
    ) -> None:

        self.unit_ability_one = unit_ability_one
        self.unit_ability_one_auto = unit_ability_one_auto
        self.unit_ability_two = unit_ability_two
        self.unit_ability_two_auto = unit_ability_two_auto
        self.unit_ability_three = unit_ability_three
        self.unit_place_close_check = unit_place_close_check
        self.unit_place_check_delay = unit_place_check_delay
        self.unit_place_timeout = unit_place_timeout
        self.unit_place_click_delay = unit_place_click_delay
        self.brook_ability_close = brook_ability_close


class av_game_settings:
    def __init__(
        self,
        lose_detection_pixel: tuple[int, int],
        lose_detection_color: tuple[int, int, int],
        game_end_pixel: tuple[int, int],
        wave_number_region: list[int],
        wait_for_spawn_pixel: tuple[int, int],
        start_pixel_cord: tuple[int, int],
        retry_pixel_cords: tuple[int, int],
        card_region: tuple[int, int, int, int],
        card_check_region: tuple[int, int, int, int],
    ) -> None:
        self.lose_detection_pixel = lose_detection_pixel
        self.lose_detection_color = lose_detection_color
        self.game_end_pixel = game_end_pixel
        self.wave_number_region = wave_number_region
        self.wait_for_spawn_pixel = wait_for_spawn_pixel
        self.start_pixel_cord = start_pixel_cord
        self.retry_pixel_cords = retry_pixel_cords
        self.card_region = card_region
        self.card_check_region = card_check_region


class av_unit_settings:
    def __init__(
        self,
        unit_place_close_check: tuple[int, int],
        unit_place_check_delay: float,
        unit_place_timeout: float,
        unit_place_click_delay: float,
        unit_place_image_confidence: float,
        unit_place_image_grayscale: bool,
        unit_place_image_region: tuple[int, int, int, int],
        unit_place_close_check_two: tuple[int, int],
        horsegirl_unit: str,
    ) -> None:

        self.unit_place_close_check = unit_place_close_check
        self.unit_place_check_delay = unit_place_check_delay
        self.unit_place_timeout = unit_place_timeout
        self.unit_place_click_delay = unit_place_click_delay
        self.unit_place_image_confidence = unit_place_image_confidence
        self.unit_place_image_grayscale = unit_place_image_grayscale
        self.unit_place_image_region = unit_place_image_region
        self.unit_place_close_check_two = unit_place_close_check_two
        self.horsegirl_unit = horsegirl_unit


class av_code_submit_settings:
    def __init__(
        self,
        mount_key: str,
        mount_delay: float,
        movement_sequence: list,
        hold_e_duration: float,
        hold_e_delay: float,
        digit_buttons: dict,
        digit_click_delay: float,
        confirm_button: tuple,
        confirm_delay: float,
    ) -> None:
        self.mount_key = mount_key
        self.mount_delay = mount_delay
        self.movement_sequence = movement_sequence
        self.hold_e_duration = hold_e_duration
        self.hold_e_delay = hold_e_delay
        self.digit_buttons = digit_buttons
        self.digit_click_delay = digit_click_delay
        self.confirm_button = confirm_button
        self.confirm_delay = confirm_delay


class Settings:
    def __init__(
        self,
        avas: av_ability_settings,
        avgs: av_game_settings,
        avus: av_unit_settings,
        avcs: av_code_submit_settings,
    ) -> None:
        self.avas = avas
        self.avgs = avgs
        self.avus = avus
        self.avcs = avcs


class SettingsLoader:
    def __init__(self, path: str | None = None) -> None:

        self.settings_path = (
            path
            if path is not None
            else os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "settings.json"
            )
        )

    def load(self) -> Settings:
        with open(self.settings_path, "r") as f:
            settings = json.load(f)

        avgs = av_game_settings(**settings["avgs"])
        avus = av_unit_settings(**settings["avus"])
        avas = av_ability_settings(**settings["avas"])
        avcs = av_code_submit_settings(**settings["avcs"])

        return Settings(avgs=avgs, avus=avus, avas=avas, avcs=avcs)


Game_Settings = None
