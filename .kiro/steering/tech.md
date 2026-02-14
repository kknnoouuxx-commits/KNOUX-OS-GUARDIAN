# KNOUX OS Guardian - Technology Stack

## Core Technologies
- **Language**: Python 3.11+
- **ML Runtime**: ONNX Runtime 1.16+
- **Database**: SQLite (built-in)
- **OS Integration**: Windows WMI, PowerShell, Win32 APIs

## Key Dependencies
```python
# System Monitoring
psutil>=5.9.0        # System metrics and process management
watchdog>=3.0.0      # File system monitoring

# Windows Integration
pywin32>=306         # Windows API access
wmi>=1.5.1           # Windows Management Instrumentation

# Machine Learning
onnxruntime>=1.16.0  # Local ML model execution
numpy>=1.24.0        # Numerical operations

# Utilities
python-dateutil>=2.8.2  # Date/time handling
PyYAML>=6.0             # Configuration parsing
requests>=2.31.0        # HTTP requests (optional/cloud features)
```

## Build & Development Commands

### Windows Execution
```batch
# Quick start
run.bat

# Run tests
test.bat

# Manual execution
python main.py
```

### Testing Commands
```batch
# Basic system test
python test_basic.py

# Test all modules
python test_all_modules.py
```

### Development Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Verify installation
python test_basic.py
```

## Architecture Patterns

### Module Pattern
Each of the 12 modules follows this structure:
```python
# Module interface pattern
class ModuleName:
    def start(self): pass
    def stop(self): pass
    def get_status(self): pass
```

### Communication Pattern
- Use `src/core/communication_bus` for inter-module communication
- Event-driven architecture with publish/subscribe
- Thread-safe message queues

### Configuration Pattern
- YAML-based configuration in `config/config.yaml`
- Access via `src/core/config.get_config()`
- Module-specific settings under `modules.*` namespace

## Code Style Guidelines

### Naming Conventions
- **Modules**: snake_case (e.g., `disk_space_orchestrator`)
- **Classes**: PascalCase (e.g., `DecisionOrchestrator`)
- **Functions**: snake_case (e.g., `get_disk_orchestrator`)
- **Variables**: snake_case (e.g., `system_metrics`)

### Documentation
- Primary language: Arabic (comments, logs, UI)
- English for technical documentation
- Include docstrings for all public functions/classes

### Error Handling
- Use structured logging (see `setup_logging()` in main.py)
- Implement rollback mechanisms via `src/core/safe_execution`
- Never crash silently - log all exceptions

## Database Schema
- Location: `database/knoux_guardian.db`
- Core tables: `system_snapshots`, `decision_artifacts`, `system_events`
- Use `src/core/database.get_database()` for access

## ML Model Integration
- Models stored in `models/onnx/`
- Use ONNX Runtime for inference
- Keep models small and optimized for local execution

## Security Considerations
- No hardcoded credentials
- Validate all OS-level operations
- Implement risk assessment before actions
- User approval required for high-risk operations