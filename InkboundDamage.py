from collections.abc import Callable, Iterable, Mapping
import threading
import time
from typing import Any
import re
import sys
import logging
import pandas as pd
import os
import pprint


import kivy

kivy.require("1.11.1")

from kivy.app import App
from kivy.uix.label import Label


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

    damageDF: pd.DataFrame

    def __init__(self, dive_number):
        logging.info("init DiveLog #" + str(dive_number))
        self.dive_number = dive_number
        self.combat_number = 0
        self.turn_number = 0
        self.players = {}
        self.entities = {}
        self.combats = {}
        self.turns = {}
        self.damageDF = pd.DataFrame(
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
            "(?:.*) (?:\d\d) (?:.) (?P<player_name>.*?) \(EntityHandle:(?P<entity_handle>.*?)\)",
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

        self.damageDF = pd.concat([self.damageDF, new_damage_df], ignore_index=True)

    def get_players(self) -> dict:
        return self.players

    def OnCombatEnter(self) -> None:
        self.combat_number += 1

    def OnTurnStart(self) -> None:
        self.turn_number += 1

    def OnCombatExit(self) -> None:
        self.turn_number = 0
        pass

    # with given dataframe sum damage for each unique action_data
    def actionDataTotals(self, combat_for_player_df: pd.DataFrame) -> dict:
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
        # print(action_data_totals)

        return action_data_totals

    def actionDataTotalsPercent(self, action_data_totals: pd.DataFrame) -> dict:
        totaldamage = sum(action_data_totals.values())

        action_data_totals_percent = {}

        for total in action_data_totals:
            action_data_totals_percent[total] = round(
                action_data_totals[total] / totaldamage * 100.00, 2
            )

    def printDataframe(self):
        # print(self.damageDF)

        logging.debug("Total Combats: %s" % str(self.damageDF["Combat"].max()))

        for combat_number in range(1, self.damageDF["Combat"].max() + 1, 1):
            combatdf = self.damageDF[self.damageDF["Combat"] == combat_number]
            # print(combat1df)

            logging.info("combat_number: " + str(combat_number))

            for player in self.players:
                combat_for_player_df = combatdf[combatdf["source_entity"] == player]
                # print(combatdf)

                action_data_totals = self.actionDataTotals(combat_for_player_df)

                combat_data_percent = self.actionDataTotalsPercent(action_data_totals)

                # logging.info(
                #     "combat_data_percent\n" + pprint.pformat(combat_data_percent) + "\n"
                # )


# TODO https://github.com/kivy/kivy/wiki/Working-with-Python-threads-inside-a-Kivy-application
class KivyApp(App):
    # Function that returns
    # the root widget
    def build(self):
        # Label with text Hello World is
        # returned as root widget
        return Label(text="Hello World !")


class DiveLogsThread(threading.Thread):
    dive_logs: list
    dive_log: DiveLog
    dive_number: int

    def __init__(self):
        threading.Thread.__init__(self)
        self.dive_logs = []
        self.dive_number = 0
        KivyApp().run()

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
                self.dive_log.printDataframe()
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
                settingHPmatch = re.search(
                    "EntityHandle:(?P<entity_handle>\d*?)\). New hp: (?P<new_hp>\d*?)$",
                    line,
                )

                entity_handle = settingHPmatch.group("entity_handle")
                new_hp = settingHPmatch.group("new_hp")

            if "healing" in line:
                healingMatch = re.search(
                    r".*EntityHandle:(?P<entity_handle>\d*?)\). Source-(?P<source>.*?) : Heal Amount-(?P<heal_amount>\d*?) : Ability-(.*?) New hp: (?P<new_hp>\d*)",
                    line,
                )
                entity_handle = healingMatch.group("entity_handle")
                source = healingMatch.group("source")
                new_hp = healingMatch.group("new_hp")

            # healing
            pass


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
            "(?P<Timestamp>.*?) \d\d I \[EventSystem\] broadcasting EventOn(?P<EventOn>.*?)-WorldState(?P<WorldState>.*?)-TargetUnitHandle:\(EntityHandle:(?P<TargetUnitHandle>\d*)\)-SourceEntityHandle:\(EntityHandle:(?P<SourceEntityHandle>\d*)\)-TargetUnitTeam:(?P<TargetUnitTeam>.*?)-IsInActiveCombat:(?P<IsInActiveCombat>.*?)-DamageAmount:(?P<DamageAmount>\d*?)-IsCriticalHit:(?P<IsCriticalHit>.*?)-WasDodged:(?P<WasDodged>.*?)-ActionData:ActionData-(?P<ActionData>.*?)-AbilityData:(?P<AbilityData>.*?)-StatusEffectData:(?P<StatusEffectData>.*?)-LootableData:(?P<LootableData>.*?)$",
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
    DiveLogsT = DiveLogsThread()
    DiveLogsT.start()

    SystemExit()
