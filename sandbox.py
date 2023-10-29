import os
import logging
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", color_codes=True)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
    )

    current_directory = os.getcwd()

    combat_for_player_df = pd.read_pickle(
        os.path.join(current_directory, "combat_for_player_df.pkl")
    )

    action_data_totals_df = pd.DataFrame({"action_data": [], "damage_amount": []})

    for action_data in combat_for_player_df["action_data"].unique():
        action_data_sum = combat_for_player_df.loc[
            combat_for_player_df["action_data"] == action_data, "damage_amount"
        ].sum()

        action_data_sum_df = pd.DataFrame(
            {"action_data": [action_data], "damage_amount": [action_data_sum]}
        )

        action_data_totals_df = pd.concat([action_data_totals_df, action_data_sum_df])

        # print(action_data_totals_df[action_data])

    action_data_totals_df.sort_values(by="damage_amount", ascending=False, inplace=True)

    logging.info(action_data_totals_df)

    f, ax = plt.subplots(figsize=(10, 10))

    sns.barplot(
        action_data_totals_df,
        x="action_data",
        y="damage_amount",
        legend=False,
    )
    # ax.set_xticklabels(ax.get_xticklabels(), rotation=40, ha="right")
    # ax.bar_label(ax.containers[0])
    plt.tight_layout()
    plt.show()
