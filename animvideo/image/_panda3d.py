from animvideo.image._img import Img
from panda3d.core import (
    loadPrcFileData,
    GraphicsPipe,
    GraphicsOutput,
    FrameBufferProperties,
    WindowProperties,
    Texture,
    NodePath,
    Vec4,
    GeomVertexFormat,
    GeomVertexData,
    Geom,
    GeomTriangles,
    GeomVertexWriter,
    GeomNode,
    OrthographicLens
)
from direct.showbase.ShowBase import ShowBase
import math
import os

# Avoid writing a log file
loadPrcFileData("", "notify-output /dev/null")

# This is a hack to prevent panda3d from exiting on its own
ShowBase.finalExit = lambda: None

base = None
def get_base():
    global base
    if base is None:
        loadPrcFileData("", "window-type offscreen")
        base = ShowBase()
    return base

class _Panda3dImage(Img):
    def __init__(self, size, color):
        self._size = size

        base = get_base()

        win_props = WindowProperties.size(size[0], size[1])
        fb_props = FrameBufferProperties()
        fb_props.set_rgba_bits(8, 8, 8, 0)
        fb_props.set_depth_bits(24)

        self._buffer = base.graphicsEngine.make_output(
            base.pipe, "offscreen buffer", -2,
            fb_props, win_props,
            GraphicsPipe.BF_refuse_window,
        )

        r, g, b = color
        self._buffer.set_clear_color(Vec4(r/255.0, g/255.0, b/255.0, 1.0))

        self._scene = NodePath("scene")
        self._camera = base.make_camera(self._buffer)
        self._camera.reparent_to(self._scene)

        lens = OrthographicLens()
        lens.set_film_size(size[0], size[1])
        lens.set_near_far(-10, 10)
        self._camera.node().set_lens(lens)
        # Position the camera so that the scene coordinates match pixel coordinates
        self._camera.set_pos(size[0]/2, size[1]/2, 1)
        self._camera.set_hpr(0, -90, 0)

    @classmethod
    def empty(cls, size: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0)) -> 'Img':
        return _Panda3dImage(size, color)

    def save(self, filename: str):
        base = get_base()
        base.graphicsEngine.render_frame()
        self._buffer.save_screenshot(filename)

    def tobytes(self) -> bytes:
        base = get_base()
        base.graphicsEngine.render_frame()
        tex = self._buffer.get_texture()
        return tex.get_ram_image_as("RGB")

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    def ring(self, color: tuple[int, int, int], inner_radius: int, outer_radius: int, center_x: int, center_y: int, rotation: float = 0.0):
        # Just draw a filled circle with outer_radius
        num_segments = 64
        format = GeomVertexFormat.get_v3c4()
        vdata = GeomVertexData('circle', format, Geom.UH_static)

        vertex = GeomVertexWriter(vdata, 'vertex')
        vcolor = GeomVertexWriter(vdata, 'color')

        # Center vertex
        vertex.add_data3(center_x, center_y, 0)
        vcolor.add_data4(color[0]/255.0, color[1]/255.0, color[2]/255.0, 1.0)

        # Outer vertices
        for i in range(num_segments + 1):
            angle = (i / num_segments) * 2 * math.pi
            dx = outer_radius * math.cos(angle)
            dy = outer_radius * math.sin(angle)
            vertex.add_data3(center_x + dx, center_y + dy, 0)
            vcolor.add_data4(color[0]/255.0, color[1]/255.0, color[2]/255.0, 1.0)

        prim = GeomTriangles(Geom.UH_static)
        for i in range(num_segments):
            prim.add_vertices(0, i + 1, i + 2)

        geom = Geom(vdata)
        geom.add_primitive(prim)

        node = GeomNode('circle_node')
        node.add_geom(geom)

        self._scene.attach_new_node(node)

    def ellipse(self, bbox: tuple[int, int, int, int], fill: tuple[int, int, int] = (0, 0, 0)):
        x0, y0, x1, y1 = bbox
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        radius_x = (x1 - x0) / 2
        radius_y = (y1 - y0) / 2

        num_segments = 64
        format = GeomVertexFormat.get_v3c4()
        vdata = GeomVertexData('ellipse', format, Geom.UH_static)

        vertex = GeomVertexWriter(vdata, 'vertex')
        vcolor = GeomVertexWriter(vdata, 'color')

        # Center vertex
        vertex.add_data3(center_x, center_y, 0)
        vcolor.add_data4(fill[0]/255.0, fill[1]/255.0, fill[2]/255.0, 1.0)

        # Outer vertices
        for i in range(num_segments + 1):
            angle = (i / num_segments) * 2 * math.pi
            dx = radius_x * math.cos(angle)
            dy = radius_y * math.sin(angle)
            vertex.add_data3(center_x + dx, center_y + dy, 0)
            vcolor.add_data4(fill[0]/255.0, fill[1]/255.0, fill[2]/255.0, 1.0)

        prim = GeomTriangles(Geom.UH_static)
        for i in range(num_segments):
            prim.add_vertices(0, i + 1, i + 2)

        geom = Geom(vdata)
        geom.add_primitive(prim)

        node = GeomNode('ellipse_node')
        node.add_geom(geom)

        self._scene.attach_new_node(node)

    def glow(self, radius: int = 79):
        pass # No-op as requested
