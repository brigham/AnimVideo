from animvideo.image._img import Img
from panda3d.core import (
    loadPrcFileData,
    GraphicsOutput,
    GraphicsPipe,
    FrameBufferProperties,
    WindowProperties,
    NodePath,
    Vec4,
    GeomVertexFormat,
    GeomVertexData,
    Geom,
    GeomTriangles,
    GeomVertexWriter,AmbientLight, VBase4,
    GeomNode,
    OrthographicLens,
    Texture,
    GeomTristrips, GeomVertexRewriter, ColorAttrib,
)
from direct.showbase.ShowBase import ShowBase
import math

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
        tex = Texture()
        tex.setup_2d_texture(self._size[0], self._size[1], Texture.T_unsigned_byte, Texture.F_rgb8)
        self._buffer.add_render_texture(tex, GraphicsOutput.RTMCopyRam)
        self._tex = tex

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

        ambient_light = AmbientLight("ambient light")
        ambient_light.set_color(VBase4(1.0, 1.0, 1.0, 1.0)) # A dim gray light
        ambient_lnp = self._scene.attach_new_node(ambient_light)

        # Tell the scene to be illuminated by this light
        self._scene.set_light(ambient_lnp)


        def _make_ring_proto(segments=128):
            fmt = GeomVertexFormat.get_v3()  # no per-vertex colors; we'll set color per-instance
            vdata = GeomVertexData('unit_ring', fmt, Geom.UH_static)
            vdata.set_num_rows((segments + 1) * 2)

            vw = GeomVertexWriter(vdata, 'vertex')
            # Unit ring with outer=1, inner=k kept in X-Y plane
            k = 0.5  # default thickness; will be overridden via nonuniform scale if needed
            for i in range(segments + 1):
                t = (i / segments) * 2.0 * math.pi
                c = math.cos(t); s = math.sin(t)
                vw.add_data3(k*c, k*s, 0)  # inner
                vw.add_data3(c, s, 0)      # outer

            prim = GeomTristrips(Geom.UH_static)
            prim.add_next_vertices((segments + 1) * 2)
            prim.close_primitive()

            geom = Geom(vdata); geom.add_primitive(prim)
            node = GeomNode('ring_proto'); node.add_geom(geom)
            return node

        self._ring_proto = NodePath(_make_ring_proto())


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
        img = self._tex.get_ram_image_as("RGB")
        if not img:
            raise RuntimeError("Texture has no RAM image")
        data = bytes(img)

        # Flip vertically to match conventional top-to-bottom rows
        w, h = self._size
        row_bytes = w * 3
        return b''.join(
            data[y*row_bytes:(y+1)*row_bytes] for y in reversed(range(h))
        )

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    def ring(self, color: tuple[int, int, int], inner_radius: int, outer_radius: int, center_x: int, center_y: int, rotation: float = 0.0):
        # Place relative to image center with rotation about image center
        cx_img = self._size[0] * 0.5
        cy_img = self._size[1] * 0.5
        dx = center_x - cx_img
        dy = center_y - cy_img
        c = math.cos(rotation); s = math.sin(rotation)
        rx = dx * c - dy * s
        ry = dx * s + dy * c
        px = cx_img + rx
        py = cy_img + ry

        inst = self._ring_proto.copy_to(self._scene)
        # Uniform scale by outer radius; then shrink inner radius via nonuniform XY scale
        # Base proto has inner/outer = k/1. To get desired inner_radius, set k = inner/outer.
        k = 0.0 if outer_radius == 0 else (inner_radius / max(outer_radius, 1e-6))
        inst.set_pos(px, py, 0)
        #inst.set_hpr(math.degrees(rotation), 0, 0)  # rotate in-plane (about Z)
        inst.set_scale(outer_radius, outer_radius, 1)
        # Adjust proto’s built-in k by additional nonuniform scale of inner vertices via TexMatrix is not available,
        # so rebuild once per distinct k buckets or keep two protos. Easiest: make one proto per k.
        inst.set_color(color[0]/255.0, color[1]/255.0, color[2]/255.0, 1.0)
        #inst.set_attrib(ColorAttrib.make_vertex())  # ensure per-instance color modulates



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
        pass
