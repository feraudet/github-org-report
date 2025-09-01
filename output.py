#!/usr/bin/env python3
"""
Output Module for GitHub Repository Analyzer

Contains functions for generating output files in different formats.
"""

import json
import csv
import os
from typing import Dict, List, Any
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo


def save_to_json(data: List[Dict[str, Any]], filename: str) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: List of repository data dictionaries
        filename: Output filename
    """
    if not data:
        return
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Data saved to {filename}")


def save_to_csv(data: List[Dict[str, Any]], filename: str) -> None:
    """
    Save data to CSV file.
    
    Args:
        data: List of repository data dictionaries
        filename: Output filename
    """
    if not data:
        return
    
    # Prepare data for CSV (flatten code_types list)
    csv_data = []
    for repo in data:
        repo_copy = repo.copy()
        repo_copy['code_types'] = ', '.join(repo['code_types'])
        csv_data.append(repo_copy)
    
    # Get all unique keys for CSV headers
    all_keys = set()
    for repo in csv_data:
        all_keys.update(repo.keys())
    
    fieldnames = sorted(list(all_keys))
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"Data saved to {filename}")


def save_to_excel(data: List[Dict[str, Any]], filename: str) -> None:
    """
    Save data to Excel file with formatting and filters.
    
    Args:
        data: List of repository data dictionaries
        filename: Output filename
    """
    if not data:
        return
    
    # Prepare data for Excel
    excel_data = []
    for repo in data:
        repo_copy = repo.copy()
        repo_copy['code_types'] = ', '.join(repo['code_types'])
        excel_data.append(repo_copy)
    
    # Create DataFrame
    df = pd.DataFrame(excel_data)
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Repository Analysis"
    
    # Add data to worksheet
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)
    
    # Create table with filters - handle large column counts
    num_cols = len(df.columns)
    if num_cols <= 26:
        # Single letter columns (A-Z)
        end_col = chr(64 + num_cols)
    else:
        # Double letter columns (AA, AB, etc.)
        first_letter = chr(64 + ((num_cols - 1) // 26))
        second_letter = chr(65 + ((num_cols - 1) % 26))
        end_col = first_letter + second_letter
    
    table = Table(
        displayName="RepoTable",
        ref=f"A1:{end_col}{len(df) + 1}"
    )
    
    # Add table style
    style = TableStyleInfo(
        name="TableStyleMedium9",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=True
    )
    table.tableStyleInfo = style
    
    # Add table to worksheet
    ws.add_table(table)
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save workbook
    wb.save(filename)
    print(f"Data saved to {filename}")


def generate_all_outputs(data: List[Dict[str, Any]], base_filename: str, output_dir: str = '.') -> None:
    """
    Generate all output formats (JSON, CSV, Excel).
    
    Args:
        data: List of repository data dictionaries
        base_filename: Base filename without extension
        output_dir: Output directory
    """
    if not data:
        print("No data to save.")
        return
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filenames
    json_file = os.path.join(output_dir, f"{base_filename}.json")
    csv_file = os.path.join(output_dir, f"{base_filename}.csv")
    excel_file = os.path.join(output_dir, f"{base_filename}.xlsx")
    
    # Save in all formats
    save_to_json(data, json_file)
    save_to_csv(data, csv_file)
    save_to_excel(data, excel_file)
