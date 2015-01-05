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
from kivy.core.image import ImageData
from kivy.core.image import Image
from kivy.graphics.texture import Texture
from kivy.core.window import Window
Window.fullscreen = False

class MaskDisplay(Widget):

    tex_path = StringProperty()
    
    def __init__(self, **kwargs):
        self.scene = ObjFile(resource_find('./models/square.obj'))
        super(MaskDisplay, self).__init__(**kwargs)
        with self.canvas:
            self.fbo = Fbo(size=self.size, clear_color=(1., 1., 1., 1.))
            self.fbo.shader.source=resource_find('./utils/mask.glsl')
        with self.fbo:
            self.cb = Callback(self.setup_gl_context)
            PushMatrix()
            self.setup_scene()
            PopMatrix()
            self.cb = Callback(self.reset_gl_context)
        self.fbo['tex1'] = 1

    def on_tex_path(self, *args):
        with self.fbo:
            BindTexture(source=self.tex_path + '/specular.bmp', index=1)
        
        
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
        self.light_pos = [0.,0.,1.,1.]
        super(Renderer, self).__init__(**kwargs)
        with self.canvas:
            self.fbo = Fbo(size=(1920,1080), clear_color=(1,0,0,0))
            self.fbo.shader.source=resource_find('./utils/ggx.glsl')
        self.fbo['rdiff'] = self.fbo['rspec'] = self.fbo['lintensity'] = 1.0
        with self.fbo:
            self.cb = Callback(self.setup_gl_context)
            PushMatrix()
            self.setup_scene()
            PopMatrix()
            self.cb = Callback(self.reset_gl_context)
        self.fbo['diffuse'] = 2
        self.fbo['specular'] = 3
        self.fbo['nmap'] = 4
        self.fbo['roughness'] = 5
        self.fbo['model_mat'] = Matrix()
        self.fbo['test_mat'] = Matrix().look_at(0,0,100,0,0,0,0,1,0)
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def on_tex_path(self, *args):
        with self.fbo:
            diffuse = Image(self.tex_path + '/diffuse.bmp')
            specular = Image(self.tex_path + '/specular.bmp')
            nmap = Image(self.tex_path + '/nmap.bmp')
            roughness = Image(self.tex_path + '/roughness.bmp')
            BindTexture(texture=diffuse.texture, index=2)
            BindTexture(texture=specular.texture, index=3)
            BindTexture(texture=nmap.texture, index=4)
            BindTexture(texture=roughness.texture, index=5)
        
    def setup_gl_context(self, *args):
        glEnable(GL_DEPTH_TEST)
        self.fbo.clear_buffer()

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)            
        
    def update_glsl(self, *largs):
        Color(1,1,1,1)
        asp = self.width / float(self.height)
        proj = Matrix().view_clip(-asp, asp, -1., 1., 1., 10000., 1.)
        self.fbo['projection_mat'] = proj
        self.fbo['view_mat'] = Matrix().look_at(self.cam_pos*math.sin(self.cam_rot),0,self.cam_pos*math.cos(self.cam_rot),0.,0.,0.,0.,1.,0.)
        self.fbo['light_pos'] = tuple(self.light_pos)
        self.fbo['threshold'] = self.threshold_widget.value
        self.fbo['normal_mat'] = (self.fbo['model_mat'].multiply(self.fbo['view_mat'])).normal_matrix()

    def setup_scene(self):
        Color(1, 1, 1, 1)
        width, height = self.fbo.texture.size
        m = list(self.scene.objects.values())[0]
        self.mesh = Mesh(
            vertices=m.vertices,
            indices=m.indices,
            fmt=m.vertex_format,
            mode='triangles',
        )

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
        
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'up':
            if modifiers and modifiers[0] == 'ctrl':
                self.light_pos[2] += 10
            else:
                if (self.cam_pos > 10):
                    self.cam_pos -= 10
        elif keycode[1] == 'down':
            if modifiers and modifiers[0] == 'ctrl':
                self.light_pos[2] -= 10
            else:
                self.cam_pos += 10
        elif keycode[1] == 'left':
            self.cam_rot -= math.pi/180
        elif keycode[1] == 'right':
            self.cam_rot += math.pi/180
        elif keycode[1] == 'w':
            self.light_pos[1] += 10
        elif keycode[1] == 's':
            self.light_pos[1] -= 10
        elif keycode[1] == 'a':
            self.light_pos[0] -= 10
        elif keycode[1] == 'd':
            self.light_pos[0] += 10
        if keycode[1] == 'escape':
            keyboard.release()
        return True        

    def update(self, active, label, value):
        if label == 'rdiff':
            self.fbo['rdiff'] = 1/float(value) if active else value
        elif label == 'rspec':
            self.fbo['rspec'] = 1/float(value) if active else value
        elif label == 'lintensity':
            self.fbo['lintensity'] = 1/float(value) if active else value
        else:
            return
        self.update_glsl()
