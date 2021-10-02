from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import ObjectProperty

from datebase import ConnDB


class GameScreen(BoxLayout):
    label = ObjectProperty()
    main_box = ObjectProperty()
    content_box = ObjectProperty()

    def __init__(self):
        super().__init__()
        self.database = ConnDB()

    def check_menu_button_click(self, button):
        for bn in self.buttons:
            if button is bn:
                bn.disabled = True
            else:
                bn.disabled = False

    def main_page(self, button):
        self.check_menu_button_click(button)

        self.content_box.clear_widgets()

        self.top_bn.text = button.text

        my_games = self.take_games()

        for game in my_games:
            sl = StackLayout(orientation='lr-bt')
            for i in game:
                btn = Button(text=str(i), width=len(str(i)) + 50, height=10, size_hint=(None, 0.1))
                sl.add_widget(btn)

            self.content_box.add_widget(sl)

    def change_label(self, button, text):
        self.check_menu_button_click(button)

        self.label.text = text

    def add_label(self, button):
        self.check_menu_button_click(button)

        self.content_box.clear_widgets()
        self.content_box.add_widget(Label(text='New'))

    def take_games(self):
        return self.database.take_games()

class MainApp(App):
    def build(self):
        return GameScreen()


if __name__ == "__main__":
    main = MainApp()
    main.run()
