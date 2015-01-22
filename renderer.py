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
        self.cnt = 0
        self.axis = 0
        self.up = True
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
#        self.canvas = RenderContext(compute_normal_mat=True)
        # TODO - Pass the shader source as an argument to the constructor
#        self.canvas.shader.source = resource_find('./utils/simple.glsl')
        # TODO - Pass the object file as an argument to the constructor
        self.scene = ObjFile(resource_find('./models/square.obj'))
        self.cam_pos = 1
        self.cam_rot = 0
        self.light_pos = [0.,-.5,1.,1.]
        super(Renderer, self).__init__(**kwargs)
        with self.canvas:
            self.fbo = Fbo(size = (1920, 1080), with_depthbuffer = True, clear_color=(1,0,0,0))
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
        self.fbo['model_mat'] = Matrix().scale(1/(50.),1/50.,1.)
#        self.fbo['model_mat'].scale((600. * 720.)/900., 720., 1.)#scale(18.77/100.,20.01/100.,1.)#scale(10.3/100.,6.48/100.,1.)#scale(12.5/100.,17.5/100,1.)
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def on_tex_path(self, *args):
        with self.fbo:
            BindTexture(source=self.tex_path + '/diffuse.bmp', index=2)
            BindTexture(source=self.tex_path + '/specular.bmp', index=3)
            BindTexture(source=self.tex_path + '/nmap.bmp', index=4)
            BindTexture(source=self.tex_path + '/roughness.bmp', index=5)
        
    def setup_gl_context(self, *args):
        glEnable(GL_DEPTH_TEST)
        self.fbo.clear_buffer()

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)            
        
    def update_glsl(self, *largs):
        if abs(self.light_pos[0]) < 1e-2 and abs(self.light_pos[1]+.5) < 1e-2:
            self.cnt += 1
        if self.cnt % 3 == 0:
            self.axis = 0 if self.axis == 1 else 1
            self.cnt += 1
        self.light_pos[self.axis] =  self.light_pos[self.axis] + 1/60. if self.up  else self.light_pos[self.axis]-1/60.
        if abs(self.light_pos[self.axis]) >= 1:
            self.up = not self.up
                    
        Color(1,1,1,1)
        asp = 600./900.#self.width / float(self.height)
        proj = Matrix().view_clip(-1, 1, -1, 1, 1, 10000, 1)
        self.fbo['projection_mat'] = proj
        self.fbo['view_mat'] = Matrix().look_at(self.cam_pos*math.sin(self.cam_rot), 0,self.cam_pos*math.cos(self.cam_rot),0,0,0,0,1,0)
        self.fbo['cam_pos'] = (self.cam_pos*math.sin(self.cam_rot), 0.,self.cam_pos*math.cos(self.cam_rot))
        self.fbo['light_pos'] = tuple(self.light_pos)
        self.fbo['threshold'] = self.threshold_widget.value
        self.fbo['normal_mat'] = (self.fbo['model_mat'].multiply(self.fbo['view_mat'])).normal_matrix()
        self.fbo['light_dir'] = (math.cos(self.light_pos[0]*math.pi/180.),0,math.sin(self.light_pos[0]*math.pi/180.))
        self.fbo['view_matinv'] = self.fbo['view_mat'].inverse()

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
        print self.light_pos
        if keycode[1] == 'up':
            if (self.cam_pos > 10):
                self.cam_pos -= 5
        elif keycode[1] == 'down':
            self.cam_pos += 5
        elif keycode[1] == 'left':
            self.cam_rot -= math.pi/180
        elif keycode[1] == 'right':
            self.cam_rot += math.pi/180
        elif keycode[1] == 'w':
            if modifiers and modifiers[0] == 'ctrl':
               self.light_pos[2] += 1
            else:
                self.light_pos[1] += 1
        elif keycode[1] == 's':
            if modifiers and modifiers[0] == 'ctrl':
                self.light_pos[2] -= 1
            else:
                self.light_pos[1] -= 1
        elif keycode[1] == 'a':
            self.light_pos[0] -= 1
        elif keycode[1] == 'd':
            self.light_pos[0] += 1
        elif keycode[1] == 't':
            self.fbo.texture.save('test.bmp')
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
