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

## 🎯 Project Overview

This project automates the processing of pilelog data from Excel files:

- **Extract**: Reads multiple Excel files with dynamic header detection
- **Transform**: Formats dates, extracts sleeve values, cleans data
- **Load**: Uploads processed data to Supabase with batch processing
- **Visualize**: Power BI dashboards connected to Supabase

## 📁 Project Structure

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
└── README.md # This file

2. Create Virtual Environment
   bash

# Windows

python -m venv venv
venv\Scripts\activate

# Mac/Linux

python3 -m venv venv
source venv/bin/activate

3. Install Dependencies
   bash
   pip install pandas python-dotenv supabase pyyaml openpyxl

4. Create Directory Structure
   bash
   mkdir src\extract src\transform src\load src\utils config scripts data\processed logs

5. Create init.py Files
   Create empty **init**.py in each src subdirectory:

bash

# Windows

echo. > src\_\_init**.py
echo. > src\extract\_\_init**.py
echo. > src\transform\_\_init**.py
echo. > src\load\_\_init**.py
echo. > src\utils\_\_init\_\_.py

6. Configure Environment
   config/.env

bash
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-supabase-api-key"

💻 Usage
Run the Pipeline
bash
python scripts/upload_pilelog.py

📊 Data Flow
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

'''
You can create the setup_project.bat file directly in your project root folder. Here's how:

Method 1: Using Notepad (Easiest)
Navigate to your project folder:

text
C:\Users\Phong\OneDrive - ICB Construction\Phong\data\DA2026\Source Code\data_analytics_project
Open Notepad:

Press Windows + R, type notepad, press Enter

Copy and paste the content:

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
Save the file:

Click File → Save As

Navigate to your project folder: C:\Users\Phong\OneDrive - ICB Construction\Phong\data\DA2026\Source Code\data_analytics_project

File name: setup_project.bat

Save as type: All Files (_._)

Click Save
'''
