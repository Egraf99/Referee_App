from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

red = [1, 0, 0, 1]
green = [0, 1, 0, 1]
blue = [0, 0, 1, 1]
purple = [1, 0, 1, 1]


class GameScreen(BoxLayout):
    def test(self, text):
        print('ok')
        self.label.text = text


class MainApp(App):
    def build(self):
        return GameScreen()


if __name__ == "__main__":
    main = MainApp()
    main.run()
