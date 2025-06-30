# Pygame type stubs for better static analysis
# This helps the type checker understand pygame's dynamic attributes

from typing import Any, Tuple, Optional, Union

def init() -> None: ...
def quit() -> None: ...

class Surface:
    def fill(self, color: Tuple[int, int, int]) -> None: ...
    def blit(self, source: 'Surface', dest: Tuple[int, int]) -> None: ...

class display:
    @staticmethod
    def set_mode(size: Tuple[int, int]) -> Surface: ...
    @staticmethod
    def set_caption(title: str) -> None: ...
    @staticmethod
    def flip() -> None: ...

class draw:
    @staticmethod
    def circle(surface: Surface, color: Tuple[int, int, int], center: Tuple[int, int], radius: int, width: int = 0) -> None: ...
    @staticmethod
    def line(surface: Surface, color: Tuple[int, int, int], start: Tuple[float, float], end: Tuple[float, float], width: int = 1) -> None: ...

class mouse:
    @staticmethod
    def get_pos() -> Tuple[int, int]: ...

class time:
    class Clock:
        def tick(self, framerate: int) -> int: ...

class font:
    class Font:
        def __init__(self, filename: Optional[str], size: int) -> None: ...
        def render(self, text: str, antialias: bool, color: Tuple[int, int, int]) -> Surface: ...

class event:
    type: int
    key: int

# Event constants
QUIT: int
KEYDOWN: int
KEYUP: int

# Key constants
K_SPACE: int
K_r: int
K_w: int
K_a: int
K_s: int
K_d: int

def get() -> list[event]: ...
