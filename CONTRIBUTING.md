# Contributing to Swarm Tank Simulation

Thank you for your interest in contributing to the Swarm Tank Simulation! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/swarm-tank-simulation.git
   cd swarm-tank-simulation
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Development Setup

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions focused and reasonably sized

### Testing

- Test your changes thoroughly
- Ensure the simulation runs without errors
- Test edge cases (empty swarms, high entity counts, etc.)

### Performance Considerations

- Profile performance-critical code
- Avoid unnecessary calculations in the main game loop
- Consider memory usage with large swarms

## Types of Contributions

### Bug Fixes

- Check existing issues before creating new ones
- Provide clear reproduction steps
- Include system information (OS, Python version, Pygame version)

### New Features

- Discuss major features in an issue first
- Keep features focused and well-documented
- Maintain backward compatibility when possible

### Documentation

- Improve code comments and docstrings
- Update README.md for new features
- Add examples and tutorials

## Code Areas

### Core Systems

- **Bot AI** (`swarm_bot.py`): Steering behaviors, role logic, reproduction
- **Game Loop** (`swarm_tank.py`): Main simulation loop, event handling, UI
- **Entities** (`entities.py`): Food, power-ups, predators
- **Roles** (`roles.py`): Bot role definitions and behaviors
- **Math** (`vector2d.py`): Vector mathematics and physics

### Potential Enhancements

- **New Bot Roles**: Medics, builders, explorers
- **Environmental Features**: Obstacles, terrain, weather
- **Advanced AI**: Machine learning, neural networks
- **Multiplayer**: Network support, competitive modes
- **Performance**: Spatial partitioning, GPU acceleration
- **Visualization**: 3D rendering, data analytics

## Submission Guidelines

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**:
   - Write clean, commented code
   - Follow existing code style
   - Test thoroughly

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add amazing feature: detailed description"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature
   ```

5. **Create a Pull Request**:
   - Provide a clear title and description
   - Reference any related issues
   - Include screenshots/videos for visual changes

## Pull Request Review Process

1. **Automated Checks**: Code style, basic functionality
2. **Manual Review**: Code quality, design, documentation
3. **Testing**: Feature testing, integration testing
4. **Approval**: Maintainer approval and merge

## Questions?

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: For security issues or private inquiries

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers and help them learn
- Focus on the code, not the person
- Give credit where credit is due

Thank you for contributing to the Swarm Tank Simulation! 🤖🎮
