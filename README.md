# Swarm Tank Simulation

A sophisticated swarm intelligence simulation featuring autonomous bots with different roles, predator-prey dynamics, and emergent behaviors.

## Features

### 🤖 **Bot Roles & Behaviors**
- **Harvesters** (Magenta): Collect food, reproduce when well-fed
- **Warriors** (Purple): Defend the swarm, attack predators, taunt enemies
- **Scouts** (Cyan): Fast scouts that find food and alert others
- **Drones** (Blue): Maintain formation and swarm cohesion
- **Leaders** (Yellow): Guide swarm movement and formation

### 🔴 **Predator System**
- **Health System**: Predators start at 50% health, gain health from kills
- **Combat**: Warriors can damage predators in close combat
- **Mortality**: Predators die from starvation or damage
- **Food Drops**: Dead predators drop 3-5 food items
- **Visual Indicators**: Health bars and kill count display

### ⚡ **Power-Up System**
- **Swarm-Wide Buffs**: Power-ups affect the entire swarm
- **Speed Boost**: +50% movement speed for 5 seconds
- **Damage Boost**: Double damage for warriors for 5 seconds
- **Energy Boost**: Restores energy to collector only
- **Visual Effects**: Pulsing rings around buffed bots

### 🧬 **Reproduction System**
- **Harvester Reproduction**: High-energy harvesters can reproduce near food
- **Genetic Inheritance**: New bots inherit active swarm buffs
- **Population Control**: Energy cost and cooldown prevent overpopulation
- **Role Diversity**: Offspring can be any role with harvester bias

### 🎮 **Interactive Controls**
- **Space**: Spawn 8 food items
- **P**: Spawn random power-up
- **B**: Manually spawn a new bot
- **Escape**: Quit game

## Installation

### Prerequisites
- Python 3.8+
- Pygame

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/swarm-tank.git
cd swarm-tank

# Install dependencies
pip install -r requirements.txt

# Run the simulation
python swarm_tank.py
```

## Game Mechanics

### **Swarm Behaviors**
- **Separation**: Avoid crowding with nearby bots
- **Alignment**: Match velocity with neighbors
- **Cohesion**: Move toward average position of neighbors
- **Food Seeking**: Prioritize food collection
- **Predator Avoidance**: Enhanced fear response to threats

### **Role-Specific Abilities**
- **Scouts**: Shout food locations to nearby bots
- **Warriors**: Taunt predators and deal combat damage
- **Harvesters**: Burst speed near food, reproduction capability
- **Drones**: Strong cohesion for formation maintenance
- **Leaders**: Balanced stats for group coordination

### **Ecosystem Balance**
- **Food Spawning**: Automatic spawning with scarcity protection
- **Predator Lifecycle**: Dynamic population with respawn mechanics
- **Energy Management**: Bots consume energy and die if starved
- **Reproduction**: Population growth balanced by predation

## Technical Details

### **Architecture**
- **Modular Design**: Separate files for different components
- **Vector Math**: Custom 2D vector class for physics
- **Role System**: Data-driven bot role configuration
- **Entity System**: Polymorphic food, power-ups, and predators

### **Performance**
- **60 FPS**: Smooth real-time simulation
- **Efficient Collision**: Optimized distance calculations
- **Dynamic Spawning**: Responsive resource management
- **Visual Effects**: Hardware-accelerated rendering

## File Structure
```
swarm-tank/
├── swarm_tank.py      # Main game loop and UI
├── swarm_bot.py       # Bot AI and behaviors
├── entities.py        # Food, power-ups, predators
├── roles.py           # Role definitions and config
├── vector2d.py        # 2D vector mathematics
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Screenshots

*Add screenshots of the simulation in action here*

## Acknowledgments

- Inspired by Craig Reynolds' Boids algorithm
- Built with Python and Pygame
- Emergent behavior research and swarm intelligence concepts

## Implementation Details

The simulation implements:

- **Vector Mathematics**: Custom Vector2D class for position and velocity calculations
- **Steering Behaviors**: Based on Craig Reynolds' boids algorithm with role-specific behaviors
- **Force-based Movement**: Realistic physics simulation with acceleration and momentum
- **Spatial Awareness**: Bots respond to neighbors, food, and threats within specific radii
- **State Management**: Complex bot states including energy, reproduction cooldowns, and buff timers
- **Dynamic Spawning**: Adaptive food and power-up generation based on game state

## Customization

You can easily modify the simulation by adjusting values in the source files:

- **Screen Settings**: Modify `SCREEN_WIDTH/HEIGHT` in `swarm_tank.py`
- **Bot Behavior**: Adjust role weights and parameters in `roles.py`
- **Physics**: Modify speed, force, and interaction radii in `swarm_bot.py`
- **Spawning Rates**: Change food and power-up generation rates in `swarm_tank.py`
- **Predator Settings**: Adjust health, damage, and AI in `entities.py`
- **Visual Effects**: Customize colors, sizes, and UI elements throughout the codebase

## Educational Value

This simulation demonstrates:

- **Emergent Behavior**: Complex swarm patterns from simple individual rules
- **Multi-agent Systems**: Coordination between different agent types
- **Predator-Prey Dynamics**: Ecological balance and survival strategies
- **Resource Management**: Competition for limited food resources
- **Real-time Physics**: Force-based movement and collision detection
- **Object-Oriented Design**: Clean, modular code architecture
- **Game Development**: Event handling, rendering, and state management with Pygame

## Performance Notes

- The simulation is optimized for 60 FPS with up to 200+ entities
- Spatial partitioning could be added for larger swarms
- GPU acceleration possible for massive scale simulations

Enjoy watching the mesmerizing patterns emerge as your swarm evolves, adapts, and survives!
