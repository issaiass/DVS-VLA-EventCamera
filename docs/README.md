# Documentation Index

Welcome to the Event Camera Simulator documentation. This folder contains detailed guides organized by topic.

## 📖 Documentation Overview

### Getting Started
- **[Quick Start](../README.md)** - Get the project running in 5 minutes
- **[Installation](../README.md#-quick-start)** - Setup and dependencies

### Understanding the System
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - How the simulator works internally
  - Algorithm explanations
  - Data flow diagrams
  - Component interactions
  - Mathematical foundations

### Using the Application
- **[API.md](API.md)** - Complete API reference
  - `VLAOptimizedDVSSimulator` class
  - All methods and parameters
  - Return values and examples
  - Error handling

- **[PARAMETERS.md](PARAMETERS.md)** - Parameter tuning guide
  - What each parameter does
  - How they interact
  - Trade-offs (speed, accuracy, noise)
  - Recommended settings by use case

### Development
- **[../src/README.md](../src/README.md)** - Source code structure
  - Where things are located
  - How to understand the code
  - Extension points

- **[../tests/README.md](../tests/README.md)** - Testing guide
  - How to run tests
  - Test organization (Unit/Integration/E2E)
  - TDD best practices
  - Writing new tests

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
  - Development setup
  - Code style and standards
  - Submitting changes
  - Review process

### Troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
  - Camera/video problems
  - Performance optimization
  - Debug mode
  - FAQ

---

## 🎯 Choose Your Path

**I'm new to the project**
→ Start with [../README.md](../README.md) (root)

**I want to use the application**
→ Read [PARAMETERS.md](PARAMETERS.md) for tuning

**I want to understand how it works**
→ Read [ARCHITECTURE.md](ARCHITECTURE.md)

**I want to integrate it into my code**
→ Read [API.md](API.md)

**I want to modify or extend it**
→ Read [../src/README.md](../src/README.md) and [CONTRIBUTING.md](CONTRIBUTING.md)

**I'm having problems**
→ Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**I want to add tests**
→ Read [../tests/README.md](../tests/README.md)

---

## 📚 Documentation Structure

```
docs/
├── README.md                 # This file (navigation)
├── ARCHITECTURE.md           # System design & algorithms
├── API.md                    # API reference
├── PARAMETERS.md             # Parameter tuning
├── CONTRIBUTING.md           # How to contribute
└── TROUBLESHOOTING.md        # FAQ & solutions
```

---

## 🔍 Quick Navigation

| Topic | Document | For |
|-------|----------|-----|
| What is this? | [README.md](../README.md) | Everyone |
| How do I run it? | [README.md#-quick-start](../README.md#-quick-start) | Users |
| How does it work? | [ARCHITECTURE.md](ARCHITECTURE.md) | Developers |
| What parameters exist? | [API.md](API.md) | Integrators |
| How do I tune it? | [PARAMETERS.md](PARAMETERS.md) | Users/Researchers |
| How do I test it? | [../tests/README.md](../tests/README.md) | Developers |
| How do I contribute? | [CONTRIBUTING.md](CONTRIBUTING.md) | Contributors |
| Something broken? | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Everyone |

---

**Last Updated**: 2026-09-15  
**Documentation Version**: 1.0.0
