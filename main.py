from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from renderer import Renderer

class RendererApp(App):
    def build(self):
        mainWindow = Builder.load_file('ui/renderer.kv')
        return mainWindow

if __name__ == "__main__":
    RendererApp().run()
