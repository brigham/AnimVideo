from . import _scene
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
    GeomVertexWriter,AmbientLight, VBase4,
    GeomNode,
    OrthographicLens,
    Texture,
    GeomTristrips,
)
from direct.showbase.ShowBase import ShowBase
import math
from typing import Callable

_radians = math.radians

def _ncircles(disc_radius, radius):
    return math.floor(math.pi / math.asin(radius / disc_radius))

class Panda3dScene(_scene.Scene):
    def create(self):
        loadPrcFileData("", "window-type offscreen")
        self._base = base = ShowBase()
        size = self.config.CANVAS_SIZE

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
        tex.setup_2d_texture(size[0], size[1], Texture.T_unsigned_byte, Texture.F_rgb8)
        self._buffer.add_render_texture(tex, GraphicsOutput.RTMCopyRam)
        self._tex = tex

        r, g, b = (0, 0, 0)
        self._buffer.set_clear_color(Vec4(r/255.0, g/255.0, b/255.0, 1.0))

        self._scene = NodePath("scene")
        self._camera = base.make_camera(self._buffer)
        self._camera.reparent_to(self._scene)

        lens = OrthographicLens()
        lens.set_film_size(size[0], size[1])
        lens.set_near_far(-10, 10)
        self._camera.node().set_lens(lens)
        # Position the camera so that the scene coordinates match pixel coordinates
        self._camera.set_pos(0, 0, 1)
        self._camera.set_hpr(0, -90, 0)

        ambient_light = AmbientLight("ambient light")
        ambient_light.set_color(VBase4(1.0, 1.0, 1.0, 1.0)) # A dim gray light
        ambient_lnp = self._scene.attach_new_node(ambient_light)

        # Tell the scene to be illuminated by this light
        self._scene.set_light(ambient_lnp)


        def _make_ring_proto(segments=16):
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

        def red_ring(parent, level, rotation):
            config = self.config
            rotprime = rotation * 6 % (2 * math.pi)
            quadnum = int(rotation * 3 / (math.pi / 2))
            cosine = abs(math.cos(rotprime))
            if quadnum % 3 == 0:
                quadrant = config.COLORS0[level % len(config.COLORS0)]
            else:
                quadrant = config.COLORS1[level % len(config.COLORS1)]
            mult = 1 - math.pow(cosine, 2)
            quadrant = (quadrant[0] * mult, quadrant[1] * mult, quadrant[2] * mult)

            self._ring(color=quadrant,
                parent=parent,
                inner_radius=config.INNER_RADIUS, outer_radius=config.OUTER_RADIUS,
                center_x=-level * config.OUTER_RADIUS * 2 - config.ADJUSTMENT,
                center_y=0,
                rotation=rotation
            )


        self._orbitals = []
        for level in range(1, self.config.LEVELS):
            # Each orbital is its own node path
            orbital = NodePath(f'orbital_{level}')
            orbital.reparent_to(self._scene)
            self._orbitals.append(orbital)
            n = _ncircles(level * self.config.OUTER_RADIUS * 2 + self.config.ADJUSTMENT, self.config.OUTER_RADIUS)
            #print(f"Level {level}: {n} circles would fit.")
            cnt = 0
            rotation = 0.0
            while rotation < 360.0:
                red_ring(parent=orbital, level=level, rotation=_radians(rotation))
                rotation += 360.0 / n
                cnt += 1
            orbital.flatten_strong()
        self._scene.analyze()

        self._time = 0.0

    @property
    def time(self) -> float:
        return self._time

    @time.setter
    def time(self, value: float):
        self._time = value
        frame = self.config.FPS * self._time
        add_rot = frame * self.config.SKIP / 2
        for level in range(1, self.config.LEVELS):
            level_rot = add_rot * (1.0 - level / self.config.LEVELS)
            self._orbitals[level - 1].set_hpr(level_rot, 0.0, 0.0)

    def _rearrange(self, data: bytes) -> bytes:
        # Flip vertically to match conventional top-to-bottom rows
        w, h = self._size
        row_bytes = w * 3
        return b''.join(
            data[y*row_bytes:(y+1)*row_bytes] for y in reversed(range(h))
        )

    def tobytes(self) -> bytes:
        base = self._base
        base.graphicsEngine.render_frame()
        img = self._tex.get_ram_image_as("RGB")
        if not img:
            raise RuntimeError("Texture has no RAM image")
        data = bytes(img)

        return self._rearrange(data)

    def consume_bytes(self, consumer: Callable[[bytes], int]):
        base = self._base
        base.graphicsEngine.render_frame()
        img = self._tex.get_ram_image_as("RGB")
        if not img:
            raise RuntimeError("Texture has no RAM image")
        data = bytes(img)

        w, h = self._size
        row_bytes = w * 3
        for y in reversed(range(h)):
            row = data[y*row_bytes:(y+1)*row_bytes]
            pos = 0
            while pos < len(row):
                if pos == 0:
                    proc = consumer(row)
                else:
                    proc = consumer(row[pos:])
                pos += proc

    def save(self, filename: str):
        base = self._base
        base.graphicsEngine.render_frame()
        self._buffer.save_screenshot(filename)


    @property
    def _size(self):
        return self.config.CANVAS_SIZE

    def _ring(self, parent: NodePath, color: tuple[int, int, int], inner_radius: int, outer_radius: int, center_x: int, center_y: int, rotation: float = 0.0):
        # Place relative to image center with rotation about image center
        dx = center_x
        dy = center_y
        c = math.cos(rotation); s = math.sin(rotation)
        rx = dx * c - dy * s
        ry = dx * s + dy * c
        px = rx
        py = ry

        inst = self._ring_proto.copy_to(parent)
        inst.set_pos(px, py, 0)
        inst.set_scale(outer_radius, outer_radius, 1)
        inst.set_color(color[0]/255.0, color[1]/255.0, color[2]/255.0, 1.0)
