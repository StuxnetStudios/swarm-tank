"""
Swarm Simulation Package

A pygame-based autonomous swarm simulation with different bot roles,
predators, and harvester-based reproduction.

Classes:
- SwarmBot: Individual bot with role-based behavior
- Predator: Lethal hunters that eliminate bots
- Food: Energy source for bots
- PowerUp: Special items with enhanced benefits
- Game: Main game controller
"""

from game import Game
from swarm_bot import SwarmBot
from entities import Food, PowerUp, Predator
from vector2d import Vector2D
from roles import BOT_ROLES, ROLE_WEIGHTS, RoleData

__all__ = [
    'Game',
    'SwarmBot', 
    'Food',
    'PowerUp',
    'Predator',
    'Vector2D',
    'BOT_ROLES',
    'ROLE_WEIGHTS',
    'RoleData'
]
