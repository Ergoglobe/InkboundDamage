import time
import re
import os

import pandas as pd

import Display
from Domain import GameLog, Player

game_log = GameLog()

# Globals
DIVE_NUMBER = 0  # starts at 0, increments by 1 each new reset_game
COMBAT_NUMBER = 0  # starts at 0, increments by 1 each time combat start is triggered
TURN_NUMBER = 0  # starts at 0, increments by 1 each time a turn is triggered, resets to 0 on combat end

logDF = pd.DataFrame({"dive": [], "combat": [], "turn": [], "timestamp": [], "log": []})


def parse():
    for line in follow():
        handle_line(line, game_log)


def follow():
    file = open(
        os.environ["USERPROFILE"] + "/AppData/LocalLow/Shiny Shoe/Inkbound/logfile.log",
        "r",
    )
    while True:
        # read last line of file
        next_line = file.readline()

        # sleep if file hasn't been updated
        if not next_line:
            Display.render(game_log)
            time.sleep(0.1)  # can probably increase this to reduce program resources
            continue

        yield next_line


# sample line
# 0T01:02:53 02 I OS: Windows 11  (10.0.22621) 64bit


def handle_line(line, game):
    global logDF

    try:
        input_line = re.match("(?P<timestamp>.*) (\d\d) (I) (?P<log>.*)", line)
        # print(input_line.groupdict())
        if input_line.group():
            input_lineDF = pd.DataFrame(
                {
                    "dive": [DIVE_NUMBER],
                    "combat": [COMBAT_NUMBER],
                    "turn": [TURN_NUMBER],
                    "timestamp": [input_line.group("timestamp")],
                    "log": [input_line.group("log")],
                }
            )
            # df = df.append( {'timestamp'}:input_line.group("log") )
            logDF = pd.concat([logDF, input_lineDF])
            # print(input_line.group("log"))

    except AttributeError:
        pass
        # print(line)
        # ignore lines that dont match the normal pattern


if __name__ == "__main__":
    parse()
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None
    ):  # more options can be specified also
        print(logDF)
