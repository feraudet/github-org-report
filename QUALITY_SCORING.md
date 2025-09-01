# Quality Scoring Configuration

This document explains the configurable quality scoring system for the GitHub repository analyzer.

## Overview

The scoring system evaluates the quality of development practices in a repository on a scale from 0 to 100 points. The configuration is located in the `quality_config.json` file.

## Configuration Structure

```json
{
  "quality_scoring": {
    "base_score": 100,
    "penalties": { ... },
    "bonuses": { ... }
  }
}
```

## Configurable Penalties

### 1. No Pull Requests (-50%)

**Configuration:**
```json
"no_prs": {
  "penalty_percent": 50,
  "message": "No pull requests found - major collaboration issue"
}
```

**Example:**
- Repository with no PRs → Final score: **50/100**
- Message: "No pull requests found - major collaboration issue - reduces score by 50 points"

### 2. PRs Without Description (-10%)

**Configuration:**
```json
"no_pr_descriptions": {
  "penalty_percent": 10,
  "threshold": 0.5,
  "message": "Poor PR documentation practices"
}
```

**Examples:**
- 30% of PRs have descriptions → 4 point penalty
- 20% of PRs have descriptions → 6 point penalty
- 60% of PRs have descriptions → No penalty

**Calculation:** `penalty = min(10, (0.5 - ratio) * 20)`

### 3. High Self-Approval Rate (-25%)

**Configuration:**
```json
"high_self_approval": {
  "penalty_percent": 25,
  "threshold": 0.5,
  "message": "High self-approval rate reduces code review quality"
}
```

**Examples:**
- 70% of PRs self-approved → 21 point penalty
- 40% of PRs self-approved → No penalty

### 4. Low External Review Rate (-15%)

**Configuration:**
```json
"low_external_review": {
  "penalty_percent": 15,
  "threshold": 0.3,
  "message": "Insufficient external code review"
}
```

**Examples:**
- 10% of PRs reviewed by others → 10 point penalty
- 50% of PRs reviewed by others → No penalty

### 5. Too Many Direct Pushes (-25%)

**Configuration:**
```json
"high_direct_pushes": {
  "penalty_percent": 25,
  "threshold": 0.3,
  "message": "Poor branch discipline with excessive direct pushes"
}
```

**Examples:**
- 50% of commits are direct pushes → 12 point penalty
- 20% of commits are direct pushes → No penalty
- Message: "Poor branch discipline with excessive direct pushes (50.0%) reduces score by 12 points"

### 6. Single Contributor (-10%)

**Configuration:**
```json
"single_contributor": {
  "penalty_percent": 10,
  "message": "Limited collaboration with single contributor"
}
```

**Example:**
- Repository with only 1 contributor → Score reduced by 10 points

### 7. Inactive Repository (-5%)

**Configuration:**
```json
"inactive_repository": {
  "penalty_percent": 5,
  "days_threshold": 365,
  "message": "Repository appears inactive"
}
```

**Examples:**
- Last commit 400 days ago → 5 point penalty
- Last commit 200 days ago → No penalty

### 8. No Commits (-10%)

**Configuration:**
```json
"no_commits": {
  "penalty_percent": 10,
  "message": "No development activity found"
}
```

## Complete Scoring Examples

### High Quality Repository (Score: 95/100)
```
✅ Good external review rate (80.0%) maintains high score
✅ Good documentation with 90.0% of PRs having descriptions  
✅ Good branch discipline with low direct push ratio (15.0%)
✅ Good collaboration with 8 contributors
✅ Recent activity maintains score
❌ High self-approval rate (60.0%) reduces score by 5 points
```

### Medium Quality Repository (Score: 65/100)
```
❌ Poor PR documentation (30.0% with descriptions) reduces score by 4 points
❌ Insufficient external code review (20.0%) reduces score by 5 points
❌ Poor branch discipline with excessive direct pushes (45.0%) reduces score by 11 points
❌ Single contributor reduces collaboration score by 10 points
❌ Repository appears inactive (450 days ago) reduces score by 5 points
```

### Low Quality Repository (Score: 25/100)
```
❌ No pull requests found - major collaboration issue - reduces score by 50 points
❌ Poor branch discipline with excessive direct pushes (80.0%) reduces score by 20 points
❌ Single contributor reduces collaboration score by 10 points
```

## Customization

### Modify Thresholds

To be stricter on direct pushes:
```json
"high_direct_pushes": {
  "penalty_percent": 30,
  "threshold": 0.2,  // Threshold lowered to 20%
  "message": "Branch discipline is critical"
}
```

### Modify Penalties

To increase penalty for PRs without descriptions:
```json
"no_pr_descriptions": {
  "penalty_percent": 15,  // Increased from 10% to 15%
  "threshold": 0.6,       // Threshold raised to 60%
  "message": "Documentation is mandatory"
}
```

### Add New Rules

```json
"too_many_files_per_pr": {
  "penalty_percent": 5,
  "threshold": 20,
  "message": "PRs should be smaller and focused"
}
```

## Usage

The `quality_config.json` file is automatically loaded when the analyzer starts. If the file is missing or corrupted, default values are used.

To test your modifications:
```bash
python main.py --org myorg --token xxx --limit 1
```

The score and detailed justification will appear in the output files (JSON, Excel, CSV).
