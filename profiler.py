import pstats
import os


current_directory = os.getcwd()


p = pstats.Stats(os.path.join(current_directory, "latest_id.prof"))
p.sort_stats("tottime").print_stats(40)
