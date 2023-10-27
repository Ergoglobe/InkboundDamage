import os
import threading
import time
import re
import logging
import pandas as pd
import pprint


from kivymd.app import MDApp
from kivymd.uix.label import MDLabel

from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import ScreenManager

from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import BoxLayout

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
        logging.info("init DiveLog #" + str(dive_number))
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
                "dive_number: "
                + str(self.dive_number)
                + " adding player: "
                + player_name
            )

    def add_damage(self, line) -> None:
        EventSystemLineParse = EventSystem(line)

        target_entity = EventSystemLineParse.TargetUnitHandle
        source_entity = EventSystemLineParse.SourceEntityHandle
        damage_amount = EventSystemLineParse.DamageAmount
        action_data = EventSystemLineParse.ActionData

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

        logging.debug(str(new_damage_dict))
        # print(new_damage)

        self.damage_df = pd.concat([self.damage_df, new_damage_df], ignore_index=True)

    def get_players(self) -> dict:
        return self.players

    def OnCombatEnter(self) -> None:
        self.combat_number += 1

    def OnTurnStart(self) -> None:
        self.turn_number += 1

    def OnCombatExit(self) -> None:
        self.turn_number = 0

    # with given dataframe sum damage for each unique action_data
    def action_data_totals(self, combat_for_player_df: pd.DataFrame) -> dict:
        action_data_totals = {}

        for action_data in combat_for_player_df["action_data"].unique():
            action_data_sum = combat_for_player_df[
                combat_for_player_df["action_data"] == action_data
            ]["damage_amount"].sum()

            action_data_totals[action_data] = action_data_sum

        # DEBUG
        # print("keys ")
        # print(action_data_totals.keys())
        # print("adt")
        # print(action_data_total2wsx1qaz's)

        return action_data_totals

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

        logging.debug("Total Combats: %s" % str(self.damage_df["Combat"].max()))

        for combat_number in range(1, self.damage_df["Combat"].max() + 1, 1):
            combatdf = self.damage_df[self.damage_df["Combat"] == combat_number]
            # print(combat1df)

            logging.info("combat_number: " + str(combat_number))

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
    def add_dive_number_label(self) -> None:
        self.add_widget(MDLabel(text="Dive #" + self.name, halign="center"))


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


# TODO https://github.com/kivy/kivy/wiki/Working-with-Python-threads-inside-a-Kivy-application
class ThreadedApp(MDApp):
    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.root.stop.set()

    def build(self):
        root_md_screen = BoxLayout(orientation="vertical")

        dive_md_screenmanager = ScreenManager()

        dive_number_dropdown_menu = DiveNumberMDDropdownMenu(dive_md_screenmanager)

        root_md_screen.add_widget(dive_number_dropdown_menu.get_menu_button())

        ## TODO: Remove this, debugging the dropdown
        for dive_number in range(1, 4, 1):
            dive_md_screenmanager.add_widget(DiveMDScreen(name=str(dive_number)))
            dive_md_screenmanager.get_screen(str(dive_number)).add_dive_number_label()
            dive_number_dropdown_menu.add_dive_number_to_dropdown_menu(dive_number)

        # Screen manager that holds the navigation rail which each display an individual dive

        root_md_screen.add_widget(dive_md_screenmanager)

        return root_md_screen


class DiveLogsThread(threading.Thread):
    dive_logs: list
    dive_log: DiveLog
    dive_number: int

    def __init__(self):
        threading.Thread.__init__(self)
        self.dive_logs = []
        self.dive_number = 0
        # ThreadedApp().run()

    def run(self):
        for line in self.follow_log():
            self.parse_line(line)

    def follow_log(self):
        file = open(
            os.environ["USERPROFILE"]
            + "/AppData/LocalLow/Shiny Shoe/Inkbound/logfile.log",
            "r",
        )
        while True:
            # read last line of file
            next_line = file.readline()

            if not next_line:
                self.dive_log.print_data_frame()
                time.sleep(10)
                continue

            yield next_line

    def parse_line(self, line):
        # maybe in the future care about solo vs not solo but for now this is fine
        if "Party run start triggered" in line:
            self.dive_number += 1
            logging.info(
                "Creating new dive log #"
                + str(self.dive_number)
                + " and adding to dive_logs"
            )
            self.dive_log = DiveLog(self.dive_number)
            self.dive_logs.append(self.dive_log)
            pass

        # the only reliable way to get player name from the logs
        # the alternative gives a hash value but doesnt connect to an entity afaik
        if "is playing ability" in line:
            self.dive_log.add_player(line)

        if "broadcasting EventOnUnitDamaged" in line:
            self.dive_log.add_damage(line)

        if "I Validating" in line:
            if "OnCombatEnter" in line:
                self.dive_log.OnCombatEnter()
            if "OnTurnStart" in line:
                self.dive_log.OnTurnStart()
            if "OnCombatExit" in line:
                self.dive_log.OnCombatExit()

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


class EventSystem:
    Timestamp: str
    EventOn: str
    WorldState: str
    TargetUnitHandle: int
    SourceEntityHandle: int
    TargetUnitTeam: str  # can ignore
    IsInActiveCombat: bool  # can ignore
    DamageAmount: int
    IsCriticalHit: bool
    WasDodged: bool
    ActionData: str  # janky
    AbilityData: str
    StatusEffectData: str
    LootableData: str  # can ignore ( for now? )

    def __init__(self, line):
        re_eventsystem = re.search(
            r"(?P<Timestamp>.*?) \d\d I \[EventSystem\] broadcasting EventOn(?P<EventOn>.*?)-WorldState(?P<WorldState>.*?)-TargetUnitHandle:\(EntityHandle:(?P<TargetUnitHandle>\d*)\)-SourceEntityHandle:\(EntityHandle:(?P<SourceEntityHandle>\d*)\)-TargetUnitTeam:(?P<TargetUnitTeam>.*?)-IsInActiveCombat:(?P<IsInActiveCombat>.*?)-DamageAmount:(?P<DamageAmount>\d*?)-IsCriticalHit:(?P<IsCriticalHit>.*?)-WasDodged:(?P<WasDodged>.*?)-ActionData:ActionData-(?P<ActionData>.*?)-AbilityData:(?P<AbilityData>.*?)-StatusEffectData:(?P<StatusEffectData>.*?)-LootableData:(?P<LootableData>.*?)$",
            line,
        )

        if re_eventsystem is None:
            logging.info(line)

        self.Timestamp = re_eventsystem.group("Timestamp")
        self.EventOn = re_eventsystem.group("EventOn")
        self.WorldState = re_eventsystem.group("WorldState")
        self.TargetUnitHandle = re_eventsystem.group("TargetUnitHandle")
        self.SourceEntityHandle = re_eventsystem.group("SourceEntityHandle")
        self.TargetUnitTeam = re_eventsystem.group("TargetUnitTeam")
        self.IsInActiveCombat = re_eventsystem.group("IsInActiveCombat")
        self.DamageAmount = re_eventsystem.group("DamageAmount")
        self.IsCriticalHit = re_eventsystem.group("IsCriticalHit")
        self.WasDodged = re_eventsystem.group("WasDodged")
        self.ActionData = re_eventsystem.group("ActionData")
        self.AbilityData = re_eventsystem.group("AbilityData")
        self.StatusEffectData = re_eventsystem.group("StatusEffectData")
        self.LootableData = re_eventsystem.group("LootableData")


if __name__ == "__main__":
    # DiveLogsThread().start()

    ThreadedApp().run()
