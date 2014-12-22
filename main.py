import sys
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from renderer import Renderer

#TODO use optparse

class RendererApp(App):

    def __init__(self, tex_path):
        super(RendererApp, self).__init__()
        self.tex_path = tex_path
    
    def build(self):
        mainWindow = Builder.load_file('ui/renderer.kv')
        mainWindow.ids['renderer'].tex_path = self.tex_path
        return mainWindow

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print 'Please provide the path to your textures'
    else:
        pass
    RendererApp(sys.argv[1]).run()
