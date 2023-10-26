from kivy.lang import Builder

from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu

from kivymd.uix.button import MDFlatButton

from kivymd.uix.screen import MDScreen


class Test(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.screen = Builder.load_string(KV)
        self.screen = MDScreen()
        menu_items = [
            {
                "text": f"Item {i}",
                "viewclass": "OneLineListItem",
                "on_release": lambda x=f"Dive {i}": self.menu_callback(x),
            }
            for i in range(5)
        ]

        MenuButton = MDFlatButton(
            id="button", text="Choose Dive", pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        self.screen.add_widget(MenuButton)

        self.menu = MDDropdownMenu(
            caller=MenuButton,
            items=menu_items,
            width_mult=4,
        )

        MenuButton.on_release = self.menu.open

    def menu_callback(self, text_item):
        print(text_item)

    def build(self):
        return self.screen


Test().run()
