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
        # Handle missing code_types field
        if 'code_types' in repo and repo['code_types']:
            repo_copy['code_types'] = ', '.join(repo['code_types'])
        else:
            repo_copy['code_types'] = ''
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
        # Handle missing code_types field
        if 'code_types' in repo and repo['code_types']:
            repo_copy['code_types'] = ', '.join(repo['code_types'])
        else:
            repo_copy['code_types'] = ''
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


def save_to_html(data: List[Dict[str, Any]], filename: str) -> None:
    """
    Save data to interactive HTML file with filters and quality configuration sliders.
    
    Args:
        data: List of repository data dictionaries
        filename: Output filename
    """
    if not data:
        return
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Repository Analysis - Interactive Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .controls {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        .control-section {{
            flex: 1;
            min-width: 300px;
        }}
        .control-section h4 {{
            margin-bottom: 15px;
            color: #495057;
            border-bottom: 2px solid #007bff;
            padding-bottom: 5px;
        }}
        .control-group {{
            display: block;
            margin: 10px 0;
        }}
        .control-group label {{
            display: block;
            font-weight: 600;
            margin-bottom: 5px;
            color: #495057;
        }}
        .slider-container {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .slider {{
            width: 150px;
        }}
        .slider-value {{
            min-width: 40px;
            font-weight: bold;
            color: #007bff;
        }}
        .filters {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 20px;
        }}
        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        .filter-group input, .filter-group select {{
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .table-container {{
            overflow-x: auto;
            padding: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .quality-score {{
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
        }}
        .score-high {{ background-color: #28a745; }}
        .score-medium {{ background-color: #ffc107; color: #212529; }}
        .score-low {{ background-color: #dc3545; }}
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .stat-label {{
            color: #6c757d;
            margin-top: 5px;
        }}
        .reset-btn {{
            background: #6c757d;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 20px;
        }}
        .reset-btn:hover {{
            background: #5a6268;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 GitHub Repository Analysis Dashboard</h1>
            <p>Interactive quality scoring with real-time configuration adjustments</p>
        </div>
        
        <div class="controls">
            <h3>Quality Configuration Sliders</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                <div class="control-section">
                    <h4>Penalties (%)</h4>
                    <div class="control-group">
                        <label>No PRs Penalty</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="no_prs_penalty" min="0" max="100" value="50">
                            <span class="slider-value" id="no_prs_value">50</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>Poor PR Descriptions</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="no_descriptions_penalty" min="0" max="30" value="15">
                            <span class="slider-value" id="no_descriptions_value">15</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>High Self-Approval</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="self_approval_penalty" min="0" max="50" value="25">
                            <span class="slider-value" id="self_approval_value">25</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>Low External Review</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="external_review_penalty" min="0" max="30" value="20">
                            <span class="slider-value" id="external_review_value">20</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>High Direct Pushes</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="direct_pushes_penalty" min="0" max="40" value="25">
                            <span class="slider-value" id="direct_pushes_value">25</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>Large PRs</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="large_prs_penalty" min="0" max="15" value="5">
                            <span class="slider-value" id="large_prs_value">5</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>Slow Review Response</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="slow_review_penalty" min="0" max="15" value="5">
                            <span class="slider-value" id="slow_review_value">5</span>
                        </div>
                    </div>
                </div>
                
                <div class="control-section">
                    <h4>Thresholds</h4>
                    <div class="control-group">
                        <label>PR Descriptions Ratio</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="descriptions_threshold" min="0.1" max="1.0" step="0.1" value="0.7">
                            <span class="slider-value" id="descriptions_threshold_value">0.7</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>Self-Approval Threshold</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="self_approval_threshold" min="0.1" max="1.0" step="0.1" value="0.5">
                            <span class="slider-value" id="self_approval_threshold_value">0.5</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>External Review Threshold</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="external_review_threshold" min="0.1" max="1.0" step="0.1" value="0.5">
                            <span class="slider-value" id="external_review_threshold_value">0.5</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>Direct Pushes Threshold</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="direct_pushes_threshold" min="0.1" max="1.0" step="0.1" value="0.3">
                            <span class="slider-value" id="direct_pushes_threshold_value">0.3</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>Large PRs Files Threshold</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="large_prs_files_threshold" min="5" max="50" value="15">
                            <span class="slider-value" id="large_prs_files_threshold_value">15</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>Slow Review Days Threshold</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="slow_review_days_threshold" min="1" max="30" value="7">
                            <span class="slider-value" id="slow_review_days_threshold_value">7</span>
                        </div>
                    </div>
                    
                    <div class="control-group">
                        <label>Inactivity Days Threshold</label>
                        <div class="slider-container">
                            <input type="range" class="slider" id="inactivity_threshold" min="30" max="365" value="180">
                            <span class="slider-value" id="inactivity_threshold_value">180</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <button class="reset-btn" onclick="resetSliders()">Reset to Defaults</button>
        </div>
        
        <div class="controls">
            <h3>Filters</h3>
            <div class="filters">
                <div class="filter-group">
                    <label>Repository Name</label>
                    <input type="text" id="nameFilter" placeholder="Filter by name...">
                </div>
                <div class="filter-group">
                    <label>Language</label>
                    <select id="languageFilter">
                        <option value="">All Languages</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Min Quality Score</label>
                    <input type="number" id="minScoreFilter" min="0" max="100" placeholder="0">
                </div>
                <div class="filter-group">
                    <label>Max Quality Score</label>
                    <input type="number" id="maxScoreFilter" min="0" max="100" placeholder="100">
                </div>
            </div>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-item">
                <div class="stat-value" id="totalRepos">0</div>
                <div class="stat-label">Total Repositories</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="avgScore">0</div>
                <div class="stat-label">Average Score</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="highQuality">0</div>
                <div class="stat-label">High Quality (≥80)</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="lowQuality">0</div>
                <div class="stat-label">Low Quality (<50)</div>
            </div>
        </div>
        
        <div class="table-container">
            <table id="repoTable">
                <thead>
                    <tr>
                        <th>Repository</th>
                        <th>Language</th>
                        <th>Quality Score</th>
                        <th>PRs</th>
                        <th>Contributors</th>
                        <th>Last Commit</th>
                        <th>Quality Justification</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Repository data
        const originalData = {json.dumps(data, indent=2)};
        let filteredData = [...originalData];
        
        // Default configuration
        const defaultConfig = {{
            no_prs_penalty: 50,
            no_descriptions_penalty: 15,
            self_approval_penalty: 25,
            external_review_penalty: 20,
            direct_pushes_penalty: 25,
            large_prs_penalty: 5,
            slow_review_penalty: 5,
            descriptions_threshold: 0.7,
            self_approval_threshold: 0.5,
            external_review_threshold: 0.5,
            direct_pushes_threshold: 0.3,
            large_prs_files_threshold: 15,
            slow_review_days_threshold: 7,
            inactivity_threshold: 180
        }};
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            populateLanguageFilter();
            setupEventListeners();
            updateTable();
            updateStats();
        }});
        
        function populateLanguageFilter() {{
            const languages = [...new Set(originalData.map(repo => repo.language || 'Unknown'))].sort();
            const select = document.getElementById('languageFilter');
            languages.forEach(lang => {{
                const option = document.createElement('option');
                option.value = lang;
                option.textContent = lang;
                select.appendChild(option);
            }});
        }}
        
        function setupEventListeners() {{
            // Slider events for penalties
            const penaltySliders = ['no_prs_penalty', 'no_descriptions_penalty', 'self_approval_penalty', 
                                  'external_review_penalty', 'direct_pushes_penalty', 'large_prs_penalty', 'slow_review_penalty'];
            
            penaltySliders.forEach(sliderId => {{
                const slider = document.getElementById(sliderId);
                const valueSpan = document.getElementById(sliderId.replace('_penalty', '_value'));
                
                slider.addEventListener('input', function() {{
                    valueSpan.textContent = this.value;
                    recalculateScores();
                }});
            }});
            
            // Slider events for thresholds
            const thresholdSliders = ['descriptions_threshold', 'self_approval_threshold', 'external_review_threshold',
                                    'direct_pushes_threshold', 'large_prs_files_threshold', 'slow_review_days_threshold', 'inactivity_threshold'];
            
            thresholdSliders.forEach(sliderId => {{
                const slider = document.getElementById(sliderId);
                const valueSpan = document.getElementById(sliderId + '_value');
                
                slider.addEventListener('input', function() {{
                    valueSpan.textContent = this.value;
                    recalculateScores();
                }});
            }});
            
            // Filter events
            document.getElementById('nameFilter').addEventListener('input', applyFilters);
            document.getElementById('languageFilter').addEventListener('change', applyFilters);
            document.getElementById('minScoreFilter').addEventListener('input', applyFilters);
            document.getElementById('maxScoreFilter').addEventListener('input', applyFilters);
        }}
        
        function recalculateScores() {{
            const config = {{
                no_prs_penalty: parseInt(document.getElementById('no_prs_penalty').value),
                no_descriptions_penalty: parseInt(document.getElementById('no_descriptions_penalty').value),
                self_approval_penalty: parseInt(document.getElementById('self_approval_penalty').value),
                external_review_penalty: parseInt(document.getElementById('external_review_penalty').value),
                direct_pushes_penalty: parseInt(document.getElementById('direct_pushes_penalty').value),
                large_prs_penalty: parseInt(document.getElementById('large_prs_penalty').value),
                slow_review_penalty: parseInt(document.getElementById('slow_review_penalty').value),
                descriptions_threshold: parseFloat(document.getElementById('descriptions_threshold').value),
                self_approval_threshold: parseFloat(document.getElementById('self_approval_threshold').value),
                external_review_threshold: parseFloat(document.getElementById('external_review_threshold').value),
                direct_pushes_threshold: parseFloat(document.getElementById('direct_pushes_threshold').value),
                large_prs_files_threshold: parseInt(document.getElementById('large_prs_files_threshold').value),
                slow_review_days_threshold: parseInt(document.getElementById('slow_review_days_threshold').value),
                inactivity_threshold: parseInt(document.getElementById('inactivity_threshold').value)
            }};
            
            originalData.forEach(repo => {{
                repo.quality_score = calculateQualityScore(repo, config);
            }});
            
            applyFilters();
        }}
        
        function calculateQualityScore(repo, config) {{
            let score = 100;
            const justifications = [];
            
            // No PRs penalty
            if ((repo.total_analyzed_prs || 0) === 0) {{
                score -= config.no_prs_penalty;
            }} else {{
                // Poor PR descriptions
                const totalPrs = repo.total_analyzed_prs || 0;
                const prsWithDesc = repo.prs_with_description || 0;
                const descRatio = totalPrs > 0 ? prsWithDesc / totalPrs : 0;
                
                if (descRatio < config.descriptions_threshold) {{
                    const penalty = Math.min(config.no_descriptions_penalty, (config.descriptions_threshold - descRatio) * 20);
                    score -= penalty;
                }}
                
                // High self-approval
                const selfApproved = repo.self_approved_prs || 0;
                const selfApprovalRatio = totalPrs > 0 ? selfApproved / totalPrs : 0;
                if (selfApprovalRatio > config.self_approval_threshold) {{
                    const penalty = Math.min(config.self_approval_penalty, selfApprovalRatio * 30);
                    score -= penalty;
                }}
                
                // Low external review
                const reviewedByOthers = repo.prs_reviewed_by_others || 0;
                const externalReviewRatio = totalPrs > 0 ? reviewedByOthers / totalPrs : 0;
                if (externalReviewRatio < config.external_review_threshold) {{
                    const penalty = Math.min(config.external_review_penalty, (config.external_review_threshold - externalReviewRatio) * 50);
                    score -= penalty;
                }}
                
                // Large PRs penalty
                const largePrs = repo.large_prs_count || 0;
                if (largePrs > 0) {{
                    const largePrsRatio = largePrs / totalPrs;
                    if (largePrsRatio > 0.3) {{
                        const penalty = Math.min(config.large_prs_penalty, largePrsRatio * 10);
                        score -= penalty;
                    }}
                }}
                
                // Slow review response penalty
                const slowReviews = repo.slow_reviews_count || 0;
                if (slowReviews > 0) {{
                    const slowReviewRatio = slowReviews / totalPrs;
                    if (slowReviewRatio > 0.3) {{
                        const penalty = Math.min(config.slow_review_penalty, slowReviewRatio * 10);
                        score -= penalty;
                    }}
                }}
            }}
            
            // High direct pushes
            const totalCommits = repo.total_commits || 0;
            const directPushes = repo.direct_pushes_to_default || 0;
            if (totalCommits > 0) {{
                const directPushRatio = directPushes / totalCommits;
                if (directPushRatio > config.direct_pushes_threshold) {{
                    const penalty = Math.min(config.direct_pushes_penalty, directPushRatio * 25);
                    score -= penalty;
                }}
            }}
            
            // Single contributor
            if ((repo.contributors_count || 0) === 1) {{
                score -= 10;
            }}
            
            // Inactivity penalty
            if (repo.last_commit_date) {{
                const lastCommitDate = new Date(repo.last_commit_date);
                const daysSinceLastCommit = (new Date() - lastCommitDate) / (1000 * 60 * 60 * 24);
                if (daysSinceLastCommit > config.inactivity_threshold) {{
                    score -= 10;
                }}
            }}
            
            return Math.max(0, Math.round(score));
        }}
        
        function applyFilters() {{
            const nameFilter = document.getElementById('nameFilter').value.toLowerCase();
            const languageFilter = document.getElementById('languageFilter').value;
            const minScore = parseInt(document.getElementById('minScoreFilter').value) || 0;
            const maxScore = parseInt(document.getElementById('maxScoreFilter').value) || 100;
            
            filteredData = originalData.filter(repo => {{
                const matchesName = !nameFilter || repo.name.toLowerCase().includes(nameFilter);
                const matchesLanguage = !languageFilter || (repo.language || 'Unknown') === languageFilter;
                const matchesScore = repo.quality_score >= minScore && repo.quality_score <= maxScore;
                
                return matchesName && matchesLanguage && matchesScore;
            }});
            
            updateTable();
            updateStats();
        }}
        
        function updateTable() {{
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';
            
            filteredData.forEach(repo => {{
                const row = document.createElement('tr');
                
                const scoreClass = repo.quality_score >= 80 ? 'score-high' : 
                                 repo.quality_score >= 50 ? 'score-medium' : 'score-low';
                
                row.innerHTML = `
                    <td><strong>${{repo.name}}</strong></td>
                    <td>${{repo.language || 'Unknown'}}</td>
                    <td><span class="quality-score ${{scoreClass}}">${{repo.quality_score}}</span></td>
                    <td>${{repo.total_analyzed_prs || 0}}</td>
                    <td>${{repo.contributors_count || 0}}</td>
                    <td>${{repo.last_commit_date_formatted || 'Never'}}</td>
                    <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;" title="${{repo.quality_justification || ''}}">${{(repo.quality_justification || '').substring(0, 100)}}...</td>
                `;
                
                tbody.appendChild(row);
            }});
        }}
        
        function updateStats() {{
            const total = filteredData.length;
            const avgScore = total > 0 ? Math.round(filteredData.reduce((sum, repo) => sum + repo.quality_score, 0) / total) : 0;
            const highQuality = filteredData.filter(repo => repo.quality_score >= 80).length;
            const lowQuality = filteredData.filter(repo => repo.quality_score < 50).length;
            
            document.getElementById('totalRepos').textContent = total;
            document.getElementById('avgScore').textContent = avgScore;
            document.getElementById('highQuality').textContent = highQuality;
            document.getElementById('lowQuality').textContent = lowQuality;
        }}
        
        function resetSliders() {{
            Object.keys(defaultConfig).forEach(key => {{
                const slider = document.getElementById(key);
                const valueSpan = document.getElementById(key.replace('_penalty', '_value'));
                slider.value = defaultConfig[key];
                valueSpan.textContent = defaultConfig[key];
            }});
            recalculateScores();
        }}
    </script>
</body>
</html>
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Interactive HTML dashboard saved to {filename}")


def generate_all_outputs(data: List[Dict[str, Any]], base_filename: str, output_dir: str = './') -> None:
    """
    Generate all output formats (JSON, CSV, Excel, HTML).
    
    Args:
        data: List of repository data dictionaries
        base_filename: Base filename without extension
        output_dir: Output directory path
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
    html_file = os.path.join(output_dir, f"{base_filename}.html")
    
    # Save to all formats
    save_to_json(data, json_file)
    save_to_csv(data, csv_file)
    save_to_excel(data, excel_file)
    save_to_html(data, html_file)
