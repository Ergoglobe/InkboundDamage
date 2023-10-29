import os
import io
import threading
import time
import re
import logging
import pandas as pd

import pprint


from kivymd.app import MDApp
from functools import partial
from kivy.clock import Clock, mainthread

from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import ScreenManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import BoxLayout

from event_system import EventSystem

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


class Entity:
    id: int
    name: str
    hp: int

    def __str__(self) -> str:
        return self.name


class Player(Entity):
    class_id: str

    def __init__(self, entity_id: int, player_name: str) -> None:
        super().__init__()
        self.id = entity_id
        self.name = player_name


class Enemy(Entity):
    group__buff: str
    group_suffix: str


class DiveLog:
    players: dict
    enemies: dict
    dive_number: int
    combat_number: int
    turn_number: int
    combats: dict
    turns: dict

    damage_df: pd.DataFrame

    def __init__(self, dive_number):
        logging.info("init DiveLog #%i", dive_number)
        self.dive_number = dive_number
        self.combat_number = 0
        self.turn_number = 0
        self.players = {}
        self.entities = {}
        self.combats = {}
        self.turns = {}
        self.damage_df = pd.DataFrame(
            columns=[
                "Combat",
                "Turn",
                "source_entity",
                "target_entity",
                "damage_amount",
                "action_data",
            ]
        )

    def get_dive_totals(self) -> dict:
        # player is an enity number stored as a key
        for player in self.players:
            all_dive_damage_for_source_entity_df = self.damage_df[
                self.damage_df["source_entity"] == player
            ]
            # TODO figure out how to add this to each player in the dataframe
            dive_damage_totals_df = self.action_data_totals(
                all_dive_damage_for_source_entity_df
            )

        return dive_damage_totals_df

    def get_dive_number(self) -> int:
        return self.dive_number

    def add_player(self, line):
        playermatch = re.search(
            r"(?:.*) (?:\d\d) (?:.) (?P<player_name>.*?) \(EntityHandle:(?P<entity_handle>.*?)\)",
            line,
        )

        player_name = playermatch.group("player_name")
        entity_handle = playermatch.group("entity_handle")

        # if entity handle not a key in players
        if int(entity_handle) not in self.players:
            # create and add a player
            player = Player(int(entity_handle), player_name)
            self.players[int(entity_handle)] = player
            logging.info(
                "dive_number #%s adding player %s", str(self.dive_number), player_name
            )

    def add_damage(self, line) -> None:
        event_system_line_parse = EventSystem(line)

        target_entity = event_system_line_parse.TargetUnitHandle
        source_entity = event_system_line_parse.SourceEntityHandle
        damage_amount = event_system_line_parse.DamageAmount
        action_data = event_system_line_parse.ActionData

        # TODO add overkill damage compare damage amount to target_entity latest HP and get overkill

        new_damage_dict = {
            "Combat": [int(self.combat_number)],
            "Turn": [int(self.turn_number)],
            "source_entity": [int(source_entity)],
            "target_entity": [int(target_entity)],
            "damage_amount": [int(damage_amount)],
            "action_data": [action_data],
        }

        new_damage_df = pd.DataFrame.from_records(new_damage_dict)

        # logging.debug(str(new_damage_dict))
        # print(new_damage)

        self.damage_df = pd.concat([self.damage_df, new_damage_df], ignore_index=True)

    def get_players(self) -> dict:
        return self.players

    def on_combat_enter(self) -> None:
        self.combat_number += 1

    def on_turn_start(self) -> None:
        self.turn_number += 1

    def on_combat_exit(self) -> None:
        self.turn_number = 0

    # with given dataframe sum damage for each unique action_data
    def action_data_totals(self, combat_for_player_df: pd.DataFrame) -> pd.DataFrame:
        action_data_totals_df = pd.DataFrame({"action_data": [], "damage_amount": []})

        # TODO maybe get list of all damage done by skill for a horizontal boxplot?

        for action_data in combat_for_player_df["action_data"].unique():
            action_data_sum = combat_for_player_df.loc[
                combat_for_player_df["action_data"] == action_data, "damage_amount"
            ].sum()

            action_data_sum_df = pd.DataFrame(
                {"action_data": [action_data], "damage_amount": [action_data_sum]}
            )

            action_data_totals_df = pd.concat(
                [action_data_totals_df, action_data_sum_df]
            )

        action_data_totals_df.sort_values(
            by="damage_amount", ascending=False, inplace=True
        )

        return action_data_totals_df

    def action_data_totals_percent(self, action_data_totals: pd.DataFrame) -> dict:
        totaldamage = sum(action_data_totals.values())

        action_data_totals_percent = {}

        for total in action_data_totals:
            action_data_totals_percent[total] = round(
                action_data_totals[total] / totaldamage * 100.00,
                2,  # percentage to 2 decimal places
            )

        return action_data_totals_percent

    def print_data_frame(self):
        # print(self.damageDF)

        # logging.debug("Total Combats: %s", self.damage_df["Combat"].max())

        for combat_number in range(1, self.damage_df["Combat"].max() + 1, 1):
            combatdf = self.damage_df[self.damage_df["Combat"] == combat_number]
            # print(combat1df)

            # logging.info("combat_number: %s", combat_number)

            for player in self.players:
                combat_for_player_df = combatdf[combatdf["source_entity"] == player]
                # print(combatdf)

                action_data_totals = self.action_data_totals(combat_for_player_df)

                combat_data_percent = self.action_data_totals_percent(
                    action_data_totals
                )

                # logging.info(
                #     "combat_data_percent\n" + pprint.pformat(combat_data_percent) + "\n"
                # )


# class DiveMDScreen:
#     Screen: MDScreen

#     def __init__(self, name) -> None:
#         self.Screen = MDScreen()
#         self.Screen.name = name
#         self.Screen.add_widget(MDLabel(text="Dive #" + name, halign="center"))

#     def get_screen(self) -> MDScreen:
#         return self.Screen


class DiveMDScreen(MDScreen):
    screen_boxlayout: BoxLayout

    def init_boxlayout(self):
        self.screen_boxlayout = BoxLayout()
        self.add_widget(self.screen_boxlayout)

    def add_dive_number_label(self) -> None:
        dive_number_label = MDLabel(text="Dive #" + self.name, halign="center")
        self.add_to_boxlayout(dive_number_label)

    def add_to_boxlayout(self, widget) -> None:
        self.screen_boxlayout.add_widget(widget)

    def add_action_data_totals(self) -> None:
        pass


# this class holds the button and the menu itself
class DiveNumberMDDropdownMenu:
    menu_button: MDFlatButton
    dive_number_dropdown_menu: MDDropdownMenu
    dive_screen_manager: ScreenManager

    def __init__(self, dive_screen_manager) -> None:
        self.menu_button = MDFlatButton(
            id="button", text="Choose Dive", size_hint=(1, 0.05)
        )

        self.dive_number_dropdown_menu = MDDropdownMenu(
            caller=self.menu_button,
            items=[],
            width_mult=4,
        )

        self.menu_button.on_release = self.dive_number_dropdown_menu.open

        # for callback to change screens we need to have the screen manager here
        self.dive_screen_manager = dive_screen_manager

    def get_menu_button(self) -> MDFlatButton:
        return self.menu_button

    def get_dropdown_menu(self) -> MDDropdownMenu:
        return self.dive_number_dropdown_menu

    def menu_callback(self, dive_number: str):
        print("Change screen to dive# " + dive_number)
        self.dive_screen_manager.current = dive_number

    def add_dive_number_to_dropdown_menu(self, dive_number: int):
        new_menu_items: list = self.dive_number_dropdown_menu.items

        new_menu_items.append(
            {
                "text": f"Dive #{str(dive_number)}",
                "viewclass": "OneLineListItem",
                "on_release": lambda x=f"{str(dive_number)}": self.menu_callback(x),
            }
        )

        self.dive_number_dropdown_menu.items = new_menu_items


class DiveLogsThread(threading.Thread):
    dive_logs: list
    dive_log: DiveLog
    dive_number: int
    log_file: io.TextIOWrapper
    log_file_fully_loaded: bool

    def __init__(self):
        threading.Thread.__init__(self)
        self.dive_logs = []
        self.dive_number = 0

        self.log_file = open(
            os.environ["USERPROFILE"]
            + "/AppData/LocalLow/Shiny Shoe/Inkbound/logfile-1.log",
            "r",
            encoding="utf-8",
        )

        self.log_file_fully_loaded = False
        # self.parse_file_until_end()

    # If next_line exists parse it, otherwise wait
    def run(self):
        while True:
            next_line = self.log_file.readline()

            if not next_line:
                # logging.info("Reached end of logfile.log")
                # self.dive_log.print_data_frame()
                self.log_file_fully_loaded = True

                time.sleep(10)

                continue
            else:
                self.log_file_fully_loaded = False
                self.parse_line(next_line)

            # TODO update gui here

    def parse_file_until_end(self) -> str:
        for next_line in self.follow_log():
            if next_line:
                self.parse_line(next_line)
            else:
                return

    def get_dive_logs(self) -> list:
        return self.dive_logs

    # TODO: Figure out how to update interface with new data
    def follow_log(self):
        while True:
            # read last line of file
            next_line = self.log_file.readline()

            if not next_line:
                self.dive_log.print_data_frame()
                time.sleep(10)
                continue

            yield next_line

    def parse_line(self, line: str):
        # Lines that arent needed to be parsed
        if "broadcasting" in line:
            if "EventOnUnitDamaged" not in line:
                return

        if "Evaluating quest progress" in line:
            return

        if "Updating quest progress" in line:
            return

        if "IncrementPlayerRecord" in line:
            return

        if "EventOrchestrationSystem" in line:
            return

        if "Evaluating quest state" in line:
            return

        if "TargetingSystem handling" in line:
            return

        if "Combat Simulation completed" in line:
            return

        if "Setting unit" in line:
            return

        # maybe in the future care about solo vs not solo but for now this is fine
        if "Party run start triggered" in line:
            self.dive_number += 1
            logging.info(
                "Creating new dive log #%i and adding to dive_logs", self.dive_number
            )
            self.dive_log = DiveLog(self.dive_number)
            self.dive_logs.append(self.dive_log)

        # the only reliable way to get player name from the logs
        # the alternative gives a hash value but doesnt connect to an entity afaik
        if "is playing ability" in line:
            self.dive_log.add_player(line)

        if "broadcasting EventOnUnitDamaged" in line:
            self.dive_log.add_damage(line)

        if "I Validating" in line:
            if "OnCombatEnter" in line:
                self.dive_log.on_combat_enter()
            if "OnTurnStart" in line:
                self.dive_log.on_turn_start()
            if "OnCombatExit" in line:
                self.dive_log.on_combat_exit()

        if "I Client unit state" in line:
            # setting
            if "Setting" in line:
                setting_hp_match = re.search(
                    r"EntityHandle:(?P<entity_handle>\d*?)\). New hp: (?P<new_hp>\d*?)$",
                    line,
                )

                entity_handle = setting_hp_match.group("entity_handle")
                new_hp = setting_hp_match.group("new_hp")

            if "healing" in line:
                healing_match = re.search(
                    r".*EntityHandle:(?P<entity_handle>\d*?)\). Source-(?P<source>.*?) : Heal Amount-(?P<heal_amount>\d*?) : Ability-(.*?) New hp: (?P<new_hp>\d*)",
                    line,
                )
                entity_handle = healing_match.group("entity_handle")
                source = healing_match.group("source")
                new_hp = healing_match.group("new_hp")

            # healing


# TODO https://github.com/kivy/kivy/wiki/Working-with-Python-threads-inside-a-Kivy-applicication
class ThreadedApp(MDApp):
    dive_logs_thread: DiveLogsThread

    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.root.stop.set()

    def add_dive(
        self, dive_md_screenmanager, dive_number_dropdown_menu, dive_number
    ) -> None:
        dive_md_screenmanager.add_widget(DiveMDScreen(name=str(dive_number)))
        dive_md_screenmanager.get_screen(str(dive_number)).add_dive_number_label()
        dive_number_dropdown_menu.add_dive_number_to_dropdown_menu(dive_number)

    def build(self):
        root_md_screen = BoxLayout(orientation="vertical")
        dive_md_screenmanager = ScreenManager()
        dive_number_dropdown_menu = DiveNumberMDDropdownMenu(dive_md_screenmanager)

        root_md_screen.add_widget(dive_number_dropdown_menu.get_menu_button())
        root_md_screen.add_widget(dive_md_screenmanager)

        self.dive_logs_thread = DiveLogsThread()
        self.dive_logs_thread.start()

        logging.info("Loading logs...")
        while not self.dive_logs_thread.log_file_fully_loaded:
            pass
        logging.info("Logs loaded until end of file")

        logging.info("Creating initial Dive Screen view...")
        ## TODO: Remove this, debugging the dropdown
        for dive_number in range(1, len(self.dive_logs_thread.get_dive_logs()) + 1):
            dive_md_screenmanager.add_widget(DiveMDScreen(name=str(dive_number)))
            dive_md_screenmanager.get_screen(str(dive_number)).init_boxlayout()
            dive_md_screenmanager.get_screen(str(dive_number)).add_dive_number_label()
            dive_number_dropdown_menu.add_dive_number_to_dropdown_menu(dive_number)
            self.dive_logs_thread.get_dive_logs()[dive_number - 1].get_dive_totals()
        return root_md_screen

    def load_initial_dive_logs(self):
        for dive_log in self.dive_logs_thread.get_dive_logs():
            logging.info("DEBUG: %s", dive_log)

            # TODO Add dive screen for each log


if __name__ == "__main__":
    ThreadedApp().run()
