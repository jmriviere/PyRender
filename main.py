import sys
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from renderer import Renderer
from kivy.properties import StringProperty

#TODO use optparse

class RendererApp(App):

    tex_path = StringProperty()

    def __init__(self, **kwargs):
        super(RendererApp, self).__init__(**kwargs)
        self.tex_path = 'derp'
    
    def build(self):
        mainWindow = Builder.load_file('ui/renderer.kv')
        return mainWindow

    def set_tex_path(self):
        print 'derpiderp', self.tex_path
        return self.tex_path

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print 'Please provide the path to your textures'
        exit()
    print 'sysargv', sys.argv[1]
    RendererApp(tex_path=sys.argv[1]).run()
