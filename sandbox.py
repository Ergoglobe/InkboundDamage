import os
import logging
import pandas as pd


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
    )

    current_directory = os.getcwd()

    combat_for_player_df = pd.read_pickle(
        os.path.join(current_directory, "combat_for_player_df.pkl")
    )

    action_data_totals_df = pd.DataFrame({"action_data": [], "damage_amount": []})

    # print(action_data_totals_df[action_data])

    action_data_totals_df = action_data_totals_df.sort_values(
        by="damage_amount", ascending=False
    )

    logging.info(action_data_totals_df)
