# AKS Cost Optimizer - Project Structure

## 📁 Organized Directory Structure

```
aks-cost-optimizer/
├── 📋 Core Application Files
│   ├── main.py                     # Main application entry point
│   ├── production_main.py          # Production entry point
│   ├── Dockerfile                  # Default secure Dockerfile (PyInstaller)
│   ├── Dockerfile.production       # Production Dockerfile
│   ├── docker-compose.yml          # Development compose file
│   ├── docker-compose.prod.yml     # Production compose file
│   └── docker-entrypoint.sh        # Main entrypoint script
│
├── 🚀 Deployment & Build Files
│   └── deploy/
│       ├── docker/                 # Docker-related files
│       │   ├── Dockerfile.bytecode             # Bytecode compilation variant
│       │   ├── Dockerfile.obfuscated           # Code obfuscation variant  
│       │   ├── Dockerfile.pyinstaller          # PyInstaller variant (backup)
│       │   ├── Dockerfile.original.backup      # Original Dockerfile backup
│       │   ├── Dockerfile.production.original.backup
│       │   ├── build-secure-containers.sh      # Multi-variant build script
│       │   ├── docker-compose.secure.yml       # Multi-variant compose
│       │   └── docker-entrypoint-binary.sh     # Binary entrypoint script
│       │
│       ├── kubernetes/             # Kubernetes manifests
│       └── terraform/              # Infrastructure as Code
│
├── 📚 Documentation
│   ├── docs/
│   │   ├── setup/                  # Setup & Configuration Guides
│   │   │   └── AZURE-SETUP.md                  # Azure credentials setup
│   │   ├── deployment/             # Deployment Documentation  
│   │   │   └── README.secure-containers.md     # Container security guide
│   │   ├── architecture/           # Architecture Documentation
│   │   │   └── database-architecture.md       # Database design
│   │   ├── features_aks.md         # AKS-specific features
│   │   ├── features_nivaya.md      # Nivaya platform features
│   │   ├── FULL_NDA.docx           # Legal documents
│   │   ├── FULL_NDA.pdf
│   │   └── PROJECT-STRUCTURE.md    # This file
│   │
├── ⚙️ Configuration
│   ├── config/
│   │   └── examples/               # Configuration examples
│   │       └── .env.example                    # Environment variables example
│   │
│   └── requirements/               # Python dependencies
│       ├── base.txt               # Base requirements
│       ├── dev.txt                # Development requirements
│       ├── prod.txt               # Production requirements
│       └── ml.txt                 # Machine learning requirements
│
├── 🏗️ Application Architecture (Clean Architecture)
│   ├── application/               # Application layer
│   │   ├── use_cases/            # Business use cases
│   │   ├── dto/                  # Data transfer objects
│   │   └── services/             # Application services
│   │
│   ├── domain/                   # Domain layer
│   │   ├── entities/             # Business entities
│   │   ├── events/               # Domain events
│   │   ├── repositories/         # Repository interfaces
│   │   ├── services/             # Domain services
│   │   └── value_objects/        # Value objects
│   │
│   ├── infrastructure/           # Infrastructure layer
│   │   ├── persistence/          # Data persistence
│   │   ├── services/             # Infrastructure services
│   │   ├── security/             # Security components
│   │   ├── caching/              # Caching layer
│   │   ├── messaging/            # Message handling
│   │   └── data/                 # Data processing
│   │
│   └── presentation/             # Presentation layer
│       ├── web/                  # Web interface
│       ├── api/                  # REST API
│       └── cli/                  # Command line interface
│
├── 🤖 Machine Learning & Analytics
│   ├── machine_learning/         # ML components
│   │   ├── core/                 # Core ML logic
│   │   ├── models/               # ML models
│   │   ├── data/                 # Training data & models
│   │   ├── training/             # Training scripts
│   │   └── inference/            # Inference engines
│   │
│   └── analytics/                # Analytics components
│       ├── collectors/           # Data collectors
│       ├── processors/           # Data processors
│       └── aggregators/          # Data aggregators
│
├── 🔗 Shared Components
│   └── shared/                   # Shared utilities
│       ├── config/               # Configuration management
│       ├── common/               # Common utilities
│       ├── standards/            # Industry standards
│       ├── utils/                # Utility functions
│       ├── logging/              # Logging utilities
│       └── monitoring/           # Monitoring utilities
│
└── 📊 Runtime Data
    └── logs/                     # Application logs
        ├── analytics/            # Analytics logs
        ├── application/          # Application logs
        └── errors/               # Error logs
```

## 🎯 Key Organization Principles

### 1. **Clean Separation**
- **Core files** remain in root for easy access
- **Deployment** files organized in `deploy/`
- **Documentation** centralized in `docs/` with subcategories
- **Configuration** examples in dedicated `config/` folder

### 2. **Docker Build Context**
- Main `Dockerfile` stays in root (default secure build)
- Alternative variants in `deploy/docker/`
- Build script handles path references automatically

### 3. **Documentation Structure**
- **`docs/setup/`** - Setup and configuration guides
- **`docs/deployment/`** - Deployment documentation  
- **`docs/architecture/`** - Technical architecture docs

### 4. **Clean Architecture Maintained**
- **Application layer** - Use cases and business logic
- **Domain layer** - Core business entities and rules
- **Infrastructure layer** - External concerns (DB, API, etc.)
- **Presentation layer** - User interfaces (Web, API, CLI)

## 🚀 Quick Start Commands

### Build & Run (Default Secure)
```bash
# From project root
docker build -t aks-cost-optimizer .
docker run -d -p 5000:5000 aks-cost-optimizer
```

### Build with Variants
```bash
# From project root
./deploy/docker/build-secure-containers.sh latest all
```

### Docker Compose
```bash
# Development
docker-compose up -d

# Production  
docker-compose -f docker-compose.prod.yml up -d

# Multi-variant testing
docker-compose -f deploy/docker/docker-compose.secure.yml up -d
```

## 📋 File Management Rules

### ✅ Keep in Root
- `main.py` - Main application entry
- `Dockerfile` - Default build (most secure)
- `docker-compose.yml` - Development compose
- `requirements.txt` - Main requirements file
- Essential scripts (`run.sh`, `makefile`)

### 📁 Organized in Folders
- **Alternative Dockerfiles** → `deploy/docker/`
- **Build scripts** → `deploy/docker/`
- **Documentation** → `docs/` (with subcategories)  
- **Config examples** → `config/examples/`
- **Deployment files** → `deploy/kubernetes/`, `deploy/terraform/`

### 🔄 Path References
- Build scripts automatically handle new paths
- Dockerfiles reference files correctly from build context
- Documentation updated with new locations

## 💡 Benefits of This Organization

1. **Cleaner root directory** - Only essential files visible
2. **Better categorization** - Docs, deployment, and config properly grouped
3. **Easier maintenance** - Related files are grouped together
4. **Professional structure** - Follows enterprise project organization patterns
5. **Preserved functionality** - All build/run commands work as before

## 🔧 Development Workflow

1. **Code changes** - Work in application layers as usual
2. **Documentation** - Update files in appropriate `docs/` subdirectories
3. **Deployment changes** - Modify files in `deploy/` folder
4. **Configuration** - Use examples from `config/examples/`
5. **Build/Test** - Run scripts from project root as before

The reorganized structure maintains all functionality while providing a much cleaner and more professional project layout!