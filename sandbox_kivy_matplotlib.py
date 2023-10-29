import os

# importing pyplot for graph plotting
from matplotlib import pyplot as plt

# importing numpy
import pandas as pd
import numpy as np
from kivy.garden.matplotlib import FigureCanvasKivyAgg

import seaborn as sns


# importing kivyapp
from kivy.app import App

# importing kivy builder
from kivy.lang import Builder


# this is the main class which will
# render the whole application
class uiApp(App):
    def build(self):
        self.str = Builder.load_string(
            """  
  
BoxLayout: 
    layout:layout 
      
    BoxLayout: 
      
        id:layout 
      
                                """
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

            action_data_totals_df = pd.concat(
                [action_data_totals_df, action_data_sum_df]
            )

            # print(action_data_totals_df[action_data])

        action_data_totals_df.sort_values(
            by="damage_amount", ascending=False, inplace=True
        )

        f, ax = plt.subplots(figsize=(10, 10))

        sns.barplot(
            action_data_totals_df,
            x="action_data",
            y="damage_amount",
            legend=False,
        )
        ax.set_xticklabels(ax.get_xticklabels(), rotation=40, ha="right")
        ax.bar_label(ax.containers[0])
        plt.tight_layout()
        # plt.show()

        # adding plot to kivy boxlayout
        self.str.layout.add_widget(FigureCanvasKivyAgg(plt.gcf()))
        return self.str


# running the application
uiApp().run()
