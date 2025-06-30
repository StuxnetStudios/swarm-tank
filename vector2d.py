"""
2D Vector class for position and velocity calculations
"""
from __future__ import annotations
import math


class Vector2D:
    """Simple 2D vector class for position and velocity calculations"""
    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Vector2D':
        return Vector2D(self.x * scalar, self.y * scalar)

    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self) -> 'Vector2D':
        mag = self.magnitude()
        if mag > 0:
            return Vector2D(self.x / mag, self.y / mag)
        return Vector2D(0, 0)

    def limit(self, max_magnitude: float) -> 'Vector2D':
        if self.magnitude() > max_magnitude:
            normalized = self.normalize()
            return normalized * max_magnitude
        return self

    def dot(self, other: 'Vector2D') -> float:
        """Calculate dot product with another vector"""
        return self.x * other.x + self.y * other.y
