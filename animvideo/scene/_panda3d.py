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
    GeomVertexWriter,
    AmbientLight,
    VBase4,
    GeomNode,
    OrthographicLens,
    PerspectiveLens,
    Texture,
    GeomTristrips,
    Shader,
    Camera,
)
from direct.filter.FilterManager import FilterManager
from direct.showbase.ShowBase import ShowBase
import math
from typing import Callable, override

_radians = math.radians

def _ncircles(disc_radius: float, radius: float) -> int:
    return math.floor(math.pi / math.asin(radius / disc_radius))

def create_ortho_lens(size: tuple[float, float]):
    lens = OrthographicLens()
    lens.set_film_size(size[0], size[1])
    lens.set_near_far(-1000, 1000)
    return lens

def create_perspective_lens(size: tuple[float, float]):
    lens = PerspectiveLens()
    lens.set_film_size(size[0], size[1])
    lens.set_near_far(0.1, 10000)
    return lens

def create_lens(size: tuple[float, float]):
    return create_perspective_lens(size)
    # return create_ortho_lens(size)

class Panda3dScene(_scene.Scene):
    @override
    def create(self):
        _ = loadPrcFileData("", "window-type offscreen")
        base: ShowBase = ShowBase()
        self._base: ShowBase = base
        size = self.config.CANVAS_SIZE

        win_props = WindowProperties()
        win_props.set_size(size[0], size[1])
        fb_props = FrameBufferProperties()
        fb_props.set_rgba_bits(8, 8, 8, 0)
        fb_props.set_depth_bits(24)

        self._base.open_default_window(props=win_props, fbprops=fb_props)

        # self._buffer: GraphicsOutput = base.graphicsEngine.make_output(
        #     base.pipe, "offscreen buffer", -2,
        #     fb_props, win_props,
        #     GraphicsPipe.BF_refuse_window,
        # )

        r, g, b = (0, 0, 0)
        self._base.win.set_clear_color(Vec4(r/255.0, g/255.0, b/255.0, 1.0))

        self._scene: NodePath = NodePath("scene")
        self._scene.reparent_to(base.render)

        self._camera: NodePath[Camera] = base.make_camera(self._base.win)
        self._camera.reparent_to(self._scene)

        lens = create_lens(size)
        self._camera.node().set_lens(lens)
        # Position the camera so that the scene coordinates match pixel coordinates
        self._camera.set_pos(1200, 0, 4000)
        self._camera.look_at(200, 0, 0)

        ambient_light = AmbientLight("ambient light")
        ambient_light.set_color(VBase4(1.0, 1.0, 1.0, 1.0)) # A dim gray light
        ambient_lnp = self._scene.attach_new_node(ambient_light)

        # Tell the scene to be illuminated by this light
        self._scene.set_light(ambient_lnp)


        def _make_ring_proto(segments: int=16):
            fmt = GeomVertexFormat.get_v3()  # no per-vertex colors; we'll set color per-instance
            vdata = GeomVertexData('unit_ring', fmt, Geom.UH_static)
            _ = vdata.set_num_rows((segments + 1) * 2)

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
            _ = prim.close_primitive()

            geom = Geom(vdata); geom.add_primitive(prim)
            node = GeomNode('ring_proto'); node.add_geom(geom)
            return node

        self._ring_proto: NodePath = NodePath(_make_ring_proto())

        def red_ring(parent: NodePath, level: int, rotation: float):
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


        self._orbitals: list[NodePath] = []
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

        self._time: float = 0.0

        self._glow(0.9)

    @property
    @override
    def time(self) -> float:
        return self._time

    @time.setter
    def time(self, value: float):
        self._time = value
        frame = self.config.FPS * self._time
        add_rot = frame * self.config.SKIP / 2
        for level in range(1, self.config.LEVELS):
            level_rot = add_rot * (1.0 - level / self.config.LEVELS)
            self._orbitals[level - 1].set_hpr(level_rot, 0.0, 0.0) # level * 0.25)
            self._orbitals[level - 1].set_pos(0.0, 0.0, level * 75)
        self._camera.set_pos(math.cos(frame / 131.0) * 1200, math.sin(frame / 131.0) * 1600, 4000)
        self._camera.look_at(200, 0, 0)


    def _rearrange(self, data: bytes) -> bytes:
        # Flip vertically to match conventional top-to-bottom rows
        w, h = self._size
        row_bytes = w * 3
        return b''.join(
            data[y*row_bytes:(y+1)*row_bytes] for y in reversed(range(h))
        )

    def _glow(self, threshold: float = 0.7):
        """Apply a lightweight bloom/glow effect as a final post-process."""

        # if 1 == 1:
        #     return
        manager = FilterManager(self._base.win, self._camera)
        tex = Texture()
        # size = self._size
        # tex.setup_2d_texture(size[0], size[1], Texture.T_unsigned_byte, Texture.F_rgb8)
        quad = manager.render_scene_into(colortex=tex)
        if not quad: # or quad:
            return
        # Simple GLSL bloom shader
        shader_src = {
            "vertex": """
            #version 120

            // This uniform must be set from your Python code.
            uniform vec4 texpad_tex;

            // 'varying' is used to pass data from the vertex to the fragment shader.
            varying vec2 v_texcoord;

            void main() {
              // gl_ModelViewProjectionMatrix and gl_Vertex are built-in inputs
              // provided by Panda3D, equivalent to mat_modelproj and vtx_position.
              gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;

              // The texture coordinate calculation remains the same, using built-in variables.
              v_texcoord = gl_Vertex.xz * texpad_tex.xy + texpad_tex.xy;
            }
            """,
            "fragment": f"""
            #version 120
            uniform sampler2D k_tex;
            varying vec2 v_texcoord;
            uniform vec2 texel_size;

            void main() {{
                vec4 color4 = texture2D(k_tex, v_texcoord);
                vec3 color = color4.rgb;

                // bright-pass
                vec3 bright = max(color - vec3({threshold}), 0.0);

                // blur approximation: 4 neighbors
                vec2 texel = texel_size;

                vec3 blur = color;
                for (int i = -5; i <= 5; i++) {{
                    for (int j = -5; j <= 5; j++) {{
                        // Skip the center pixel (0,0 offset)
                        if (i == 0 && j == 0) {{
                            continue;
                        }}

                        // Calculate the offset and sample the texture
                        vec2 offset = vec2(float(i) * texel.x, float(j) * texel.y);
                        blur += texture2D(k_tex, v_texcoord + offset).rgb;
                    }}
                }}
                blur *= (1.0 / 121.0);

                vec3 glow = color + blur + bright;
                gl_FragColor = vec4(glow, 1.0);
                }}
            """,
        }


        shader = Shader.make(Shader.SL_GLSL,
                                shader_src["vertex"],
                                shader_src["fragment"])
        if shader.getErrorFlag():
                print("Shader compilation failed. Check your shader files for syntax errors.")
                # You might also want to print more details about the error if available
                # (e.g., from the console output or logs if Panda3D provides them)
        else:
            print("Shader compiled successfully.")
            quad.set_shader(shader)
            quad.set_shader_input("k_tex", tex)        # Create a fullscreen quad that samples the offscreen texture
            texpad = (0.5 - (tex.get_pad_x_size() / tex.x_size / 2), 0.5 - (tex.get_pad_y_size() / tex.y_size / 2))
            print(texpad, tex.x_size, tex.y_size, self._size, tex.get_pad_x_size(), tex.get_pad_y_size())
            quad.set_shader_input("texpad_tex", texpad)
            quad.set_shader_input("texel_size", (1.0/self._size[0], 1.0/self._size[1]))



    @override
    def tobytes(self) -> bytes:
        base = self._base
        base.graphicsEngine.render_frame()
        ss = self._base.win.get_screenshot()
        if not ss:
            raise RuntimeError("Could not get screenshot")
        img = ss.get_ram_image_as("RGB")
        data = bytes(img)

        return self._rearrange(data)

    @override
    def consume_bytes(self, consumer: Callable[[bytes], int]):
        base = self._base
        base.graphicsEngine.render_frame()
        ss = self._base.win.get_screenshot()
        if not ss:
            raise RuntimeError("Could not get screenshot")
        img = ss.get_ram_image_as("RGB")
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

    @override
    def save(self, filename: str):
        base = self._base
        base.graphicsEngine.render_frame()
        _ = self._base.win.save_screenshot(filename)

    @property
    def _size(self):
        return self.config.CANVAS_SIZE

    def _ring(self, parent: NodePath, color: tuple[float, float, float], inner_radius: int, outer_radius: int, center_x: int, center_y: int, rotation: float = 0.0):
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
