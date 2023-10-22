from collections.abc import Callable, Iterable, Mapping
import threading
import time
from typing import Any
import re
import sys
import logging
from FileOps import follow_log
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


class Entity:
    id: int
    name: str
    hp: int


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

    def __init__(self, dive_number):
        logging.info("init DiveLog #" + str(dive_number))
        self.dive_number = dive_number
        self.combat_number = 0
        self.turn_number = 0
        self.players = {}
        self.entities = {}

    def get_dive_number(self) -> int:
        return self.dive_number

    def add_player(self, entity_handle, player_name):
        logging.info(
            "dive_number: " + str(self.dive_number) + " adding player: " + player_name
        )
        player = Player(int(entity_handle), player_name)
        self.players.update({entity_handle: player})

    def get_players(self) -> dict:
        return self.players


class DiveLogsThread(threading.Thread):
    dive_logs: list
    dive_log: DiveLog
    dive_number: int

    def __init__(self):
        threading.Thread.__init__(self)
        self.dive_logs = []
        self.dive_number = 0

    def run(self):
        for line in follow_log():
            self.parse_line(line)

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
            playermatch = re.search(
                "(?:.*) (?:\d\d) (?:.) (?P<player_name>.*?) \(EntityHandle:(?P<entity_handle>.*?)\)",
                line,
            )

            player_name = playermatch.group("player_name")
            entity_handle = playermatch.group("entity_handle")

            if int(entity_handle) not in self.dive_log.get_players():
                self.dive_log.add_player(int(entity_handle), player_name)

        if "I Validating" in line:
            # OnCombatEnter
            # OnTurnStart
            # OnCombatExit
            pass

        if "I Client unit state" in line:
            # setting
            # healing
            pass


if __name__ == "__main__":
    DiveLogsT = DiveLogsThread()
    DiveLogsT.start()

    SystemExit()
