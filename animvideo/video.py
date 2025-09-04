import ffmpeg
import abc
import subprocess
from typing import Tuple
from animvideo.image import Img

class AbstractVideoProducer(abc.ABC):
    def __init__(self, output_path: str, size: Tuple[int, int], fps: int):
        self.output_path = output_path
        self.size = size
        self.fps = fps

    @abc.abstractmethod
    def add_frame(self, frame: Img, number: int):
        pass

    @abc.abstractmethod
    def finalize(self):
        pass

class NoopProducer(AbstractVideoProducer):
    def __init__(self):
        super().__init__("", (0, 0), 0)

    def add_frame(self, frame: Img, number: int):
        pass

    def finalize(self):
        pass

class GlobVideoProducer(AbstractVideoProducer):
    def __init__(self, output_path: str, size: Tuple[int, int], fps: int, prefix: str):
        super().__init__(output_path, size, fps)
        self.prefix = prefix

    def add_frame(self, frame: Img, number: int):
        frame.save(f"{self.prefix}_{number:06d}.png")

    def finalize(self):
        stream = ffmpeg.input('red_ring_*.png', pattern_type='glob', framerate=self.fps).filter('scale', self.size[0] // 2, -1)
        stream.output(self.output_path, pix_fmt='yuv420p', sws_flags='lanczos').overwrite_output().run()
        print("Video created successfully!")

class FFmpegVideoProducer(AbstractVideoProducer):
    """
    A video producer that creates a video by piping raw image frames
    directly to an FFmpeg subprocess, avoiding intermediate files.
    """
    def __init__(self, output_path: str, size: Tuple[int, int], output_size: Tuple[int, int], fps: int):
        super().__init__(output_path, size, fps)
        width, height = self.size

        # The FFmpeg command to receive raw video data from stdin
        command = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}',
            '-pix_fmt', 'rgb24',
            '-r', str(self.fps),
            '-i', '-',  # Input from stdin
            '-c:v', 'libx264',
            # scale down
            '-vf', f'scale={output_size[0]}:{output_size[1]}',
            '-sws_flags', 'lanczos',
            '-pix_fmt', 'yuv420p',
            self.output_path
        ]

        # Start the FFmpeg subprocess with a pipe to its stdin
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE)

    def add_frame(self, frame: Img, number: int):
        """
        Adds a single Pillow image frame to the video stream.
        The frame must be in 'RGB' mode and match the specified size.
        """
        # Convert the Pillow image to raw bytes and write to the pipe
        if not self.process.stdin:
            raise ValueError("Video stream is not initialized.")
        self.process.stdin.write(frame.tobytes())

    def finalize(self):
        """
        Closes the video stream and waits for FFmpeg to finish processing.
        """
        if self.process.stdin:
            self.process.stdin.close()
        self.process.wait()
        print(f"Video '{self.output_path}' finalized successfully. ✨")
