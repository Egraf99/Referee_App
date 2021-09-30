from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen


class GameScreen(BoxLayout):
    def change_label(self, text):
        self.label.text = text

    def add_label(self):
        self.main_box.clear_widgets()
        self.main_box.add_widget(Label(text='New'))

class MainApp(App):
    def build(self):
        return GameScreen()


if __name__ == "__main__":
    main = MainApp()
    main.run()
