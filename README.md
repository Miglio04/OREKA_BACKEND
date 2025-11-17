# Oreka Backend

A FastAPI-based backend server for processing restaurant financial data including POS exports and invoices, with automated KPI calculations and dashboard analytics.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Codebase Structure](#codebase-structure)
- [Installation](#installation)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Coding Guidelines](#coding-guidelines)
- [Contributing](#contributing)

## 🎯 Overview

Oreka Backend is a Python-based API server designed to process and analyze restaurant financial data. It accepts CSV files from POS (Point of Sale) systems and PDF invoices, performs comprehensive KPI calculations, and provides dashboard analytics for business intelligence.

## ✨ Features

- **Multi-format File Processing**
  - CSV file processing (Cachier POS exports)
  - PDF invoice parsing and text extraction
  - Automatic encoding detection for CSV files
  
- **KPI Calculations**
  - Revenue analytics by area and payment method
  - Receipt analysis and average receipt value
  - Discount rate calculations
  - COGS (Cost of Goods Sold) computation
  - Gross margin and operating margin analysis
  - ROI and inventory turnover metrics
  
- **Dashboard Analytics**
  - Real-time statistics dashboard
  - File processing history
  - Comprehensive financial summaries

- **RESTful API**
  - File upload endpoint with validation
  - Dashboard data retrieval
  - Health check endpoint
  - CORS-enabled for frontend integration

## 📁 Codebase Structure

```
OREKA_BACKEND/
├── src/
│   └── oreka_backend/
│       ├── __init__.py              # Package initialization
│       ├── main.py                  # FastAPI application and endpoints
│       ├── models.py                # Pydantic data models
│       ├── upload.py                # File processing logic (FileProcessor class)
│       ├── kpi_calculations.py      # KPI calculation functions
│       └── pdfExtractor.py          # PDF processing with Mistral AI
├── tests/                           # Test directory (to be implemented)
├── uploads/                         # Processed files storage (auto-created)
├── pyproject.toml                   # Project dependencies and metadata
├── uv.lock                          # UV lock file for reproducible installs
├── .python-version                  # Python version specification (3.13)
└── README.md                        # This file
```

### Module Descriptions

#### `main.py`
FastAPI application entry point defining:
- API endpoints (`/upload`, `/dashboard`, `/health`)
- CORS middleware configuration
- Request/response handling
- Error handling and HTTP exceptions

#### `models.py`
Pydantic models for data validation:
- `POSLine`: POS transaction line items
- `SalesInvoice`, `PurchaseInvoice`: Invoice data structures
- `LaborCost`, `FixedCost`: Cost tracking models
- `InventorySnapshot`, `CapitalSnapshot`: Financial snapshots
- `PriceListItem`, `ReorderLevel`: Inventory management

#### `upload.py`
`FileProcessor` class handling:
- File upload processing (CSV/PDF)
- CSV parsing with multiple encoding support
- PDF text extraction using PyMuPDF
- Invoice information extraction with regex patterns
- JSON storage and retrieval of processed files
- KPI computation summaries

#### `kpi_calculations.py`
Financial calculation functions:
- `kpi_pos_only()`: Revenue and receipt analytics
- `compute_cogs()`: Cost of goods sold calculation
- `gross_margin_by_area()`: Margin analysis by business area
- `operating_margin_total()`: Operating profit calculations
- `roi_monthly()`, `inventory_turnover()`: Financial metrics
- Decimal precision handling for accurate financial math

#### `pdfExtractor.py`
PDF processing with AI integration:
- Text extraction from PDF documents
- Mistral AI integration for invoice interpretation
- Appwrite storage integration
- Structured JSON output for invoice data

## 🚀 Installation

### Prerequisites

- Python 3.13+
- [UV](https://github.com/astral-sh/uv) package manager

### Setup with UV

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd OREKA_BACKEND
   ```

2. **Install dependencies using UV**
   ```bash
   uv sync
   ```
   This will:
   - Create a virtual environment
   - Install all dependencies from `pyproject.toml`
   - Generate/update `uv.lock` for reproducibility

3. **Activate the virtual environment**
   ```bash
   source .venv/bin/activate  # On Linux/Mac
   # or
   .venv\Scripts\activate     # On Windows
   ```

4. **Set up environment variables** (for PDF processing)
   ```bash
   export MISTRAL_API_KEY="your-mistral-api-key"
   export BUCKET_ID="your-bucket-id"
   export PROJECT_ID="your-project-id"
   export APPWRITE_ENDPOINT="your-appwrite-endpoint"
   export API_KEY="your-appwrite-api-key"
   ```

## 💻 Development

### Running the Development Server

```bash
# From root repo
fastapi dev src/my_project/main.py
```

The API will be available at `http://localhost:8000`

### Interactive API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`

### Adding Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Update dependencies
uv sync
```

### Running Tests

```bash
# Run tests with pytest
uv run pytest
```

## 📡 API Documentation

### Endpoints

#### `GET /`
Health check endpoint
- **Response**: `{"message": "Oreka Backend API"}`

#### `GET /health`
Server health status
- **Response**: `{"status": "healthy"}`

#### `POST /upload`
Upload and process CSV or PDF files
- **Request**: `multipart/form-data` with `file` field
- **Accepts**: `.csv` (POS exports), `.pdf` (invoices)
- **Response**: Processed data with KPIs

#### `GET /dashboard`
Retrieve dashboard summary with all computations
- **Response**: Complete analytics including revenue, receipts, and file statistics

#### `GET /dashboard/files`
List all processed files
- **Response**: Array of processed file metadata

## 📝 Coding Guidelines

This project follows strict coding standards using modern Python tooling.

### UV Package Manager

**UV** is the primary package manager for this project. It provides:
- Fast dependency resolution
- Reproducible builds via lock files
- Virtual environment management
- Compatible with standard Python packaging

#### Common UV Commands

```bash
# Install dependencies
uv sync

# Add a package
uv add requests

# Add dev dependency
uv add --dev pytest

# Remove a package
uv remove package-name

# Update all dependencies
uv sync --upgrade

# Run a command in the virtual environment
uv run python script.py

# Show installed packages
uv pip list
```

### Ruff Linter & Formatter

**Ruff** is used for both linting and code formatting. It's extremely fast and replaces multiple tools (Black, isort, Flake8, etc.).

#### Running Ruff

```bash
# Install ruff
uv add --dev ruff

# Check for issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Check and format in one command
uv run ruff check --fix . && uv run ruff format .
```

### Code Style Guidelines

1. **Type Hints**: Always use type hints for function parameters and return values
   ```python
   def process_data(items: list[Item]) -> dict[str, Any]:
       ...
   ```

2. **Pydantic Models**: Use Pydantic for data validation
   ```python
   from pydantic import BaseModel, Field
   
   class Item(BaseModel):
       name: str
       price: float = Field(ge=0)
   ```

3. **Decimal for Financial Calculations**: Always use `Decimal` for money/financial math
   ```python
   from decimal import Decimal
   revenue = Decimal("100.50")
   ```

4. **Async/Await**: Use async functions for I/O operations
   ```python
   async def process_file(file: UploadFile) -> dict:
       contents = await file.read()
   ```

5. **Error Handling**: Use FastAPI's HTTPException for API errors
   ```python
   from fastapi import HTTPException
   raise HTTPException(status_code=400, detail="Invalid file")
   ```

6. **Documentation**: Write clear docstrings
   ```python
   def calculate_kpi(data: list[POSLine]) -> dict:
       """
       Calculate KPIs from POS data.
       
       Args:
           data: List of POS transaction lines
           
       Returns:
           Dictionary containing calculated KPIs
       """
   ```

### Pre-commit Workflow

```bash
# Before committing
uv run ruff check --fix .
uv run ruff format .
uv run pytest  # when tests are available

# Then commit
git add .
git commit -m "Your message"
```

## 🤝 Contributing

1. Follow the coding guidelines above
2. Ensure all code is formatted with Ruff
3. Add type hints to all functions
4. Write tests for new features
5. Update documentation as needed

## 📄 License

[Add your license information here]

## 👥 Authors

[Add author information here]

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Package management by [UV](https://github.com/astral-sh/uv)
- Code quality with [Ruff](https://github.com/astral-sh/ruff)
- PDF processing with [PyMuPDF](https://pymupdf.readthedocs.io/)
- AI integration with [Mistral AI](https://mistral.ai/)
