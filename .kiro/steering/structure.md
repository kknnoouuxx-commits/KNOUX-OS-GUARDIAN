# KNOUX OS Guardian - Project Structure

## Root Directory Layout
```
KNOUX_OS_Guardian/
├── .kiro/                    # Kiro AI assistant configuration
│   └── steering/            # Steering documents (this file)
├── .project/                # Project metadata
├── .vscode/                 # VS Code settings
├── api/                     # API layer (Postman collection, REST endpoints)
├── config/                  # Configuration files
├── data/                    # Runtime data
│   ├── logs/               # Application logs
│   └── snapshots/          # System snapshots
├── database/                # SQLite database files
├── docs/                    # Documentation
├── files/                   # System files (edits, memories)
├── models/                  # Machine Learning models
│   ├── onnx/               # ONNX models for local inference
│   └── training/           # Training data and scripts
├── scripts/                 # Utility scripts
├── src/                     # Source code
│   ├── core/               # Core infrastructure
│   └── modules/            # 12 specialized modules
├── tests/                   # Test suites
│   ├── integration/        # Integration tests
│   └── unit/               # Unit tests
└── *.md, *.py, *.bat       # Root-level files
```

## Core Source Structure (`src/core/`)

### Decision Engine (`src/core/decision_engine/`)
- Central decision-making logic
- ML model integration
- Rule evaluation and explanation generation

### Communication Bus (`src/core/communication_bus/`)
- Inter-module messaging system
- Event publishing/subscription
- Thread-safe message queues

### Safe Execution (`src/core/safe_execution/`)
- Snapshot management
- Rollback mechanisms
- Sandbox execution environment

### Telemetry (`src/core/telemetry/`)
- Anonymous data collection (opt-in)
- PII sanitization
- Buffered transmission

### Configuration (`src/core/config.py`)
- YAML configuration parsing
- Settings management
- Environment-specific overrides

### Database (`src/core/database.py`)
- SQLite connection management
- Schema versioning
- Data access patterns

## Module Structure (`src/modules/`)

### 12 Specialized Modules
Each module follows the same pattern:
```
src/modules/{module_name}/
└── __init__.py            # Module interface and factory function
```

### Module List
1. `disk_space_orchestrator` - Storage management
2. `update_guardian` - Update management
3. `performance_optimizer` - Performance tuning
4. `network_monitor` - Network monitoring
5. `security_hardener` - Security enhancement
6. `driver_health_manager` - Driver management
7. `forensic_analyzer` - Crash analysis
8. `thermal_controller` - Temperature management
9. `power_manager` - Power management
10. `application_lifecycle_curator` - Application management
11. `registry_guardian` - Registry protection
12. `backup_orchestrator` - Backup management

## Data Directory Structure

### Logs (`data/logs/`)
- Application runtime logs
- Rotated by size/age
- UTF-8 encoding for Arabic support

### Snapshots (`data/snapshots/`)
- System state snapshots
- Pre-action backups
- Rollback points

### Database (`database/`)
- SQLite database files
- Schema migrations
- Backup copies

## Configuration Files

### Main Config (`config/config.yaml`)
- System-wide settings
- Module enable/disable flags
- Threshold values and intervals

### Environment-specific
- Development vs production settings
- User-specific overrides
- Secret management (future)

## Test Structure

### Unit Tests (`tests/unit/`)
- Individual component tests
- Mock external dependencies
- Fast execution

### Integration Tests (`tests/integration/`)
- Module interaction tests
- End-to-end workflows
- System-level validation

### Root Test Files
- `test_basic.py` - Basic system verification
- `test_all_modules.py` - Comprehensive module testing

## Build & Deployment Files

### Windows Scripts
- `run.bat` - Quick start script
- `test.bat` - Test execution script

### Python Entry Points
- `main.py` - Primary application entry
- `requirements.txt` - Dependency specification

## Development Guidelines

### Adding New Modules
1. Create directory under `src/modules/{module_name}/`
2. Implement `__init__.py` with factory function
3. Follow the standard module interface pattern
4. Add configuration section in `config/config.yaml`
5. Create unit tests in `tests/unit/`

### File Organization
- Keep related files together
- Use clear, descriptive names
- Follow Python package conventions
- Maintain Arabic/English documentation balance

### Import Patterns
```python
# Core imports
from src.core.config import get_config
from src.core.database import get_database

# Module imports
from src.modules.{module_name} import get_{module_name}
```

### Testing Strategy
- Unit tests for each module
- Integration tests for core workflows
- Property-based tests for critical logic
- Arabic language testing for UI components