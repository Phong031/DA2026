# Data Analytics Project - Pilelog ETL Pipeline

A modular ETL (Extract, Transform, Load) pipeline for processing pilelog data from multiple Excel files and uploading to Supabase, with Power BI integration for dashboards.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)
- [Usage](#usage)
- [Key Components](#key-components)
- [Data Flow](#data-flow)
- [Common Issues & Solutions](#common-issues--solutions)
- [Extending the Pipeline](#extending-the-pipeline)
- [Performance Metrics](#performance-metrics)
- [Batch File Setup](#batch-file-setup)

## 🎯 Project Overview

This project automates the processing of pilelog data from Excel files:

- **Extract**: Reads multiple Excel files with dynamic header detection
- **Transform**: Formats dates, extracts sleeve values, cleans data
- **Load**: Uploads processed data to Supabase with batch processing
- **Visualize**: Power BI dashboards connected to Supabase

## 📁 Project Structure

```Bash
data_analytics_project/
├── src/ # Source code
│ ├── extract/ # Data extraction modules
│ │ ├── excel_loader.py # Basic Excel operations
│ │ └── pilelog_extractor.py # Pilelog-specific extraction
│ ├── transform/ # Data transformation modules
│ │ └── pilelog_transformer.py # Date/sleeve transformations
│ ├── load/ # Data loading modules
│ │ ├── supabase_client.py # Supabase connection manager
│ │ └── uploader.py # Batch upload logic
│ └── utils/ # Utility modules
│ └── config_loader.py # Configuration management
├── config/ # Configuration files
│ ├── .env # Environment variables (credentials)
│ ├── config.yaml # Main pipeline configuration
│ └── pilelog_files.yaml # List of Excel file paths
├── scripts/ # Executable scripts
│ └── upload_pilelog.py # Main ETL pipeline script
├── data/ # Data directory
│ └── processed/ # Processed data output
├── logs/ # Log files
├── requirements.txt # Python dependencies
├── setup_project.bat # Windows setup batch file
└── README.md # This file
```

## 🚀 Setup Instructions

### 1. Create Project Directory

````bash
mkdir data_analytics_project
cd data_analytics_project
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install pandas python-dotenv supabase pyyaml openpyxl
```
### 4. Create Directory Structure
```bash
# Windows
mkdir src\extract src\transform src\load src\utils config scripts data\processed logs

# Mac/Linux
mkdir -p src/extract src/transform src/load src/utils config scripts data/processed logs
```

### 5. Create __init__.py Files
```Bash
Create empty __init__.py in each src subdirectory:

# Windows
echo. > src\__init__.py
echo. > src\extract\__init__.py
echo. > src\transform\__init__.py
echo. > src\load\__init__.py
echo. > src\utils\__init__.py

# Mac/Linux
touch src/__init__.py
touch src/extract/__init__.py
touch src/transform/__init__.py
touch src/load/__init__.py
touch src/utils/__init__.py
```

## 💻 Usage
### Run the Pipeline
```bash
python scripts/upload_pilelog.py

## 🔧 Key Components
1. Excel Loader (excel_loader.py)
Load Excel files with or without headers

Get sheet names

Load sheets as raw data for header detection

2. Pilelog Extractor (pilelog_extractor.py)
Dynamically finds header rows containing required columns

Extracts job numbers from first row

Adds metadata (Job Number, Wall Name)

Processes all sheets in each file

3. Pilelog Transformer (pilelog_transformer.py)
Converts Calc Conc to float with 2 decimals

Formats dates to dd/mm/yyyy

Extracts temporary and permanent sleeve lengths using regex:

Patterns: temp Xm, perm Xm, X + jensen Y

4. Supabase Client (supabase_client.py)
Singleton pattern for single connection

Initializes with URL and API key

Provides client instance

5. Uploader (uploader.py)
Batch upload with configurable batch size

Overwrite mode: deletes existing data using any column

Append mode: adds new records

Rate limiting between batches (0.05s delay)

6. Config Loader (config_loader.py)
Loads YAML configuration files

Merges main config with file paths config

Handles missing files and parsing errors
```

## 📊 Data Flow
text
Excel Files (50+ files)
    ↓
[Extract] Dynamic header detection
    ↓
Raw Data (Job Number + Wall Name added)
    ↓
[Combine] Concatenate all sheets
    ↓
Raw Combined CSV (data/processed/)
    ↓
[Transform] Date formatting + Sleeve extraction
    ↓
Cleaned Data
    ↓
[Load] Batch upload to Supabase
    ↓
Power BI Dashboard

## 🪟 Batch File Setup
Create setup_project.bat in Project Root
Navigate to your project folder:

text
C:\Users\Phong\OneDrive - ICB Construction\Phong\data\DA2026\Source Code\data_analytics_project
Open Notepad (Windows + R → notepad)

Copy and paste the following content:
```Bash
batch
@echo off
echo ============================================
echo Setting up Data Analytics Project
echo ============================================

echo.
echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo To run the pipeline:
echo python scripts\upload_pilelog.py
echo.
pause
```

### Save as setup_project.bat:

File → Save As

Navigate to your project folder

Save as type: All Files (*.*)

File name: setup_project.bat

Click Save

### Run the Batch File
Double-click setup_project.bat in File Explorer

### What the Batch File Does:

Creates Python virtual environment

Activates the environment

Installs all required dependencies from requirements.txt

Provides instructions for running the pipeline




````
