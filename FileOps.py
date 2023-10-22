import os


def follow_log():
    file = open(
        os.environ["USERPROFILE"] + "/AppData/LocalLow/Shiny Shoe/Inkbound/logfile.log",
        "r",
    )
    while True:
        # read last line of file
        next_line = file.readline()

        yield next_line
