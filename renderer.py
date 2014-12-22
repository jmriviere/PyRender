import math
import sys
sys.path.append('./utils')
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.resources import resource_find
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import *
from kivy.graphics import *
from objloader import ObjFile
from kivy.interactive import InteractiveLauncher
from kivy.core.image import Image
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.core.window import Window
Window.fullscreen = False

class MaskDisplay(Widget):
    
    def __init__(self, **kwargs):
        self.scene = ObjFile(resource_find('./models/square.obj'))
        super(MaskDisplay, self).__init__(**kwargs)
        with self.canvas:
            self.fbo = Fbo(size=self.size, compute_normal_mat=True, clear_color=(1., 1., 1., 1.))
            self.fbo.shader.source=resource_find('./utils/mask.glsl')
        with self.fbo:
            BindTexture(source='./textures/specular.bmp', index=1)
            self.cb = Callback(self.setup_gl_context)
            PushMatrix()
            self.setup_scene()
            PopMatrix()
            self.cb = Callback(self.reset_gl_context)
        self.fbo['tex1'] = 1

    def setup_gl_context(self, *args):
        glEnable(GL_DEPTH_TEST)
        
    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

    def update_glsl(self, *largs):
        if largs:
            self.fbo['threshold'] = largs[0]
        else:
            self.fbo['threshold'] = 0
        Color(1,1,1,1)
        asp = self.width / float(self.height)
        proj = Matrix().view_clip(-50, 50, -50, 50, 1, 10000, 1)
        self.fbo['projection_mat'] = proj
        self.fbo['modelview_mat'] = Matrix().look_at(0,0,1,0,0,0,0,1,0)
#        self.rect.pos = self.pos
#        self.rect.size = self.size
        
    def setup_scene(self):
        Color(1, 1, 1, 1)
        PushMatrix()
        m = list(self.scene.objects.values())[0]
        UpdateNormalMatrix()
        self.mesh = Mesh(
            vertices=m.vertices,
            indices=m.indices,
            fmt=m.vertex_format,
            mode='triangles',
        )
        PopMatrix()


class Renderer(Widget):

    threshold_widget = ObjectProperty()
    tex_path = StringProperty()
    
    def __init__(self, **kwargs):
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
#        self.canvas = RenderContext(compute_normal_mat=True)
        # TODO - Pass the shader source as an argument to the constructor
#        self.canvas.shader.source = resource_find('./utils/simple.glsl')
        # TODO - Pass the object file as an argument to the constructor
        self.scene = ObjFile(resource_find('./models/square.obj'))
        self.cam_pos = 100
        self.cam_rot = 0
        self.light_mat = Matrix()
        super(Renderer, self).__init__(**kwargs)
        with self.canvas:
            self.fbo = Fbo(size=(1920,1080), compute_normal_mat=True, clear_color=(1,0,0,0))
            self.fbo.shader.source=resource_find('./utils/simple.glsl')
        with self.fbo:
            BindTexture(source='./textures/diffuse.bmp', index=1)
            BindTexture(source='./textures/specular.bmp', index=2)
            BindTexture(source='./textures/nmap.bmp', index=3)
            BindTexture(source='./textures/roughness.bmp', index=4)
            self.cb = Callback(self.setup_gl_context)
            PushMatrix()
            self.setup_scene()
            PopMatrix()
            self.cb = Callback(self.reset_gl_context)
        self.fbo['diffuse'] = 1
        self.fbo['specular'] = 2
        self.fbo['nmap'] = 3
        self.fbo['roughness'] = 4
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def setup_gl_context(self, *args):
        glEnable(GL_DEPTH_TEST)
        self.fbo.clear_buffer()

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)            
        
    def update_glsl(self, *largs):
        Color(1,1,1,1)
        asp = self.width / float(self.height)
        proj = Matrix().view_clip(-asp, asp, -1, 1, 1, 10000, 1)
        self.fbo['projection_mat'] = proj
        self.fbo['modelview_mat'] = Matrix().look_at(self.cam_pos*math.sin(self.cam_rot),0,self.cam_pos*math.cos(self.cam_rot),0,0,0,0,1,0)
        self.fbo['diffuse_light'] = (1.0, 1.0, 0.8)
        self.fbo['ambient_light'] = (0.1, 0.1, 0.1)
        self.fbo['light_mat'] = self.light_mat
        self.fbo['threshold'] = self.threshold_widget.value
#        self.canvas['lintensity']


    def setup_scene(self):
        Color(1, 1, 1, 1)
        self.light_mat.translate(0,0,100)
        PushMatrix()
        m = list(self.scene.objects.values())[0]
        UpdateNormalMatrix()
        self.mesh = Mesh(
            vertices=m.vertices,
            indices=m.indices,
            fmt=m.vertex_format,
            mode='triangles',
        )
        PopMatrix()

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
        
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'up':
            if modifiers and modifiers[0] == 'ctrl':
               self.light_mat.translate(0,0,10)
            else:
                if (self.cam_pos > 10):
                    self.cam_pos -= 10
        elif keycode[1] == 'down':
            if modifiers and modifiers[0] == 'ctrl':
                self.light_mat.translate(0,0,-10)
            else:
                self.cam_pos += 10
        elif keycode[1] == 'left':
            self.cam_rot += math.pi/180
        elif keycode[1] == 'right':
            self.cam_rot -= math.pi/180
        elif keycode[1] == 'w':
            self.light_mat.translate(0,10,0)
        elif keycode[1] == 's':
            self.light_mat.translate(0,-10,0)
        elif keycode[1] == 'a':
            self.light_mat.translate(-10,0,0)
        elif keycode[1] == 'd':
            self.light_mat.translate(10,0,0)
            
        
        if keycode[1] == 'escape':
            keyboard.release()
        return True        
