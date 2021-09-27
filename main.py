from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

red = [1, 0, 0, 1]
green = [0, 1, 0, 1]
blue = [0, 0, 1, 1]
purple = [1, 0, 1, 1]


class Container(BoxLayout):
    def test(self):
        print('test success!')


class MainApp(App):
    def build(self):
        return Container()


if __name__ == "__main__":
    main = MainApp()
    main.run()
