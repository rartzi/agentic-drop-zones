---
name: Generate More Training Data
allowed-tools: Bash, Read, Write
description: Analyze data patterns and generate additional synthetic training data
---

# Generate More Training Data

This command analyzes patterns in existing data files (CSV, JSONL) and generates additional synthetic training data based on those patterns. Uses bash commands or inline uv python to append data efficiently without loading large files into memory.

## Instructions

- IMPORTANT: You can use inline astral uv python code (with any libraries you need) for data processing. Use `uv run python --with pandas --with <whatever library you need> -c "import pandas as pd; print(\"whatever you want here\")"` 
  - Example: `uv run --with pandas --with faker python -c "import pandas as pd; from faker import Faker; fake = Faker(); print(fake.name())"`
- IMPORTANT: Both bash commands and uv python are acceptable - choose the most efficient approach for each task
- IMPORTANT: When generating synthetic data, ensure variety and realistic patterns

## Variables

DROPPED_FILE_PATH: [[FILE_PATH]]
DROPPED_FILE_PATH_ARCHIVE: agentic_drop_zone/training_data_zone/drop_zone_file_archive/
DATA_OUTPUT_DIR: agentic_drop_zone/training_data_zone/data_output/<date_time>/
    - This is the directory where all generated data will be saved
    - The date_time is the current date and time in the format YYYY-MM-DD_HH-MM-SS
NUM_NEW_ROWS: 25
    - Default number of new data rows to generate
    - Can be overridden if specified in the dropped file
SAMPLE_SIZE: 50
    - Number of rows to sample for pattern analysis (keeps context window small)
    - Use Read with only a specific number of rows to keep the context window small

## Workflow

- Create output directory: `DATA_OUTPUT_DIR/<date_time>/`
- Determine file format by extension (.csv or .jsonl)
- Copy the original file to output directory: `cp DROPPED_FILE_PATH DATA_OUTPUT_DIR/<date_time>/original_<filename>`

### Pattern Analysis Phase

- Extract a sample for analysis (to keep context window small):
  
  **Option 1: Using bash commands**
  - For CSV: `head -n SAMPLE_SIZE DROPPED_FILE_PATH > DATA_OUTPUT_DIR/<date_time>/sample.csv`
  - For JSONL: `head -n SAMPLE_SIZE DROPPED_FILE_PATH > DATA_OUTPUT_DIR/<date_time>/sample.jsonl`
  
  **Option 2: Using uv python**
  ```bash
  # For CSV
  uv run --with pandas python -c "
  import pandas as pd
  df = pd.read_csv('DROPPED_FILE_PATH', nrows=100)
  df.to_csv('DATA_OUTPUT_DIR/<date_time>/sample.csv', index=False)
  print(f'Sampled {len(df)} rows for analysis')
  "
  
  # For JSONL
  uv run --with pandas python -c "
  import pandas as pd
  df = pd.read_json('DROPPED_FILE_PATH', lines=True, nrows=100)
  df.to_json('DATA_OUTPUT_DIR/<date_time>/sample.jsonl', orient='records', lines=True)
  print(f'Sampled {len(df)} rows for analysis')
  "
  ```

- Read and analyze ONLY the sample file to determine:
  - Data schema/structure
  - Field types and patterns
  - Value distributions and constraints
  - Any relationships between fields

**For CSV files:**
- Identify column headers from first line
- Detect data types for each column (numeric, text, date, boolean, etc.)
- Analyze value ranges for numeric columns
- Identify patterns in text fields (emails, phone numbers, IDs, etc.)
- Check for categorical values and their distributions

**For JSONL files:**
- Parse each line as a separate JSON object
- Identify all keys and their data types
- Detect enumerated values and their frequencies
- Identify any ID patterns or sequences
- Note: Each line must be a complete, valid JSON object

### Data Generation Phase

- Based on the pattern analysis, generate `NUM_NEW_ROWS` new data entries
- Write the new data to a separate file:
  - For CSV: `DATA_OUTPUT_DIR/<date_time>/new_rows.csv` (without headers)
  - For JSONL: `DATA_OUTPUT_DIR/<date_time>/new_rows.jsonl`

  **Example using uv python with faker:**
  ```bash
  # Generate synthetic CSV data
  uv run --with pandas --with faker python -c "
  import pandas as pd
  from faker import Faker
  import random
  fake = Faker()
  
  # Generate 25 rows of synthetic data based on analyzed patterns
  data = []
  for i in range(25):
      row = {
          'id': i + 1000,  # Continue from existing IDs
          'name': fake.name(),
          'email': fake.email(),
          'age': random.randint(22, 65),
          'department': random.choice(['Engineering', 'Marketing', 'Sales', 'Support'])
      }
      data.append(row)
  
  df = pd.DataFrame(data)
  df.to_csv('DATA_OUTPUT_DIR/<date_time>/new_rows.csv', index=False, header=False)
  print(f'Generated {len(df)} new rows')
  "
  ```

- Generated data should:
  - Follow the same structure as the original
  - Maintain realistic value distributions
  - Preserve relationships between fields
  - Use similar patterns for IDs, dates, etc.
  - Include variation to avoid exact duplicates
  - Maintain data integrity constraints observed in original

### Append Phase

- Create the extended dataset by appending new rows to a copy of the original:

  **Option 1: Using bash commands**
  
  For CSV:
  ```bash
  # Copy original to extended file
  cp DATA_OUTPUT_DIR/<date_time>/original_<filename> DATA_OUTPUT_DIR/<date_time>/extended_data.csv
  
  # Append new rows (skip header if present in new_rows.csv)
  tail -n +2 DATA_OUTPUT_DIR/<date_time>/new_rows.csv >> DATA_OUTPUT_DIR/<date_time>/extended_data.csv
  ```
  
  For JSONL:
  ```bash
  # Copy original to extended file
  cp DATA_OUTPUT_DIR/<date_time>/original_<filename> DATA_OUTPUT_DIR/<date_time>/extended_data.jsonl
  
  # Append new rows
  cat DATA_OUTPUT_DIR/<date_time>/new_rows.jsonl >> DATA_OUTPUT_DIR/<date_time>/extended_data.jsonl
  ```

  **Option 2: Using uv python**
  
  For CSV:
  ```bash
  uv run --with pandas python -c "
  import pandas as pd
  
  # Read original and new data
  original = pd.read_csv('DATA_OUTPUT_DIR/<date_time>/original_<filename>')
  new_rows = pd.read_csv('DATA_OUTPUT_DIR/<date_time>/new_rows.csv', header=None, names=original.columns)
  
  # Combine and save
  extended = pd.concat([original, new_rows], ignore_index=True)
  extended.to_csv('DATA_OUTPUT_DIR/<date_time>/extended_data.csv', index=False)
  print(f'Extended dataset: {len(original)} -> {len(extended)} rows')
  "
  ```
  
  For JSONL:
  ```bash
  uv run --with pandas python -c "
  import pandas as pd
  
  # Read original and new data
  original = pd.read_json('DATA_OUTPUT_DIR/<date_time>/original_<filename>', lines=True)
  new_rows = pd.read_json('DATA_OUTPUT_DIR/<date_time>/new_rows.jsonl', lines=True)
  
  # Combine and save
  extended = pd.concat([original, new_rows], ignore_index=True)
  extended.to_json('DATA_OUTPUT_DIR/<date_time>/extended_data.jsonl', orient='records', lines=True)
  print(f'Extended dataset: {len(original)} -> {len(extended)} rows')
  "
  ```

### Reporting Phase

- Count rows in original and extended files:
  ```bash
  # For CSV (subtract 1 for header)
  ORIGINAL_COUNT=$(($(wc -l < DATA_OUTPUT_DIR/<date_time>/original_<filename>) - 1))
  EXTENDED_COUNT=$(($(wc -l < DATA_OUTPUT_DIR/<date_time>/extended_data.csv) - 1))
  
  # For JSONL
  ORIGINAL_COUNT=$(wc -l < DATA_OUTPUT_DIR/<date_time>/original_<filename>)
  EXTENDED_COUNT=$(wc -l < DATA_OUTPUT_DIR/<date_time>/extended_data.jsonl)
  ```

- Create analysis report `DATA_OUTPUT_DIR/<date_time>/data_analysis_report.md`:
  - Original file name and format
  - Sample size analyzed
  - Detected schema/structure
  - Field types and patterns identified
  - Value distributions observed
  - Generation strategy used
  - Number of rows: original vs extended

- Create metadata file `DATA_OUTPUT_DIR/<date_time>/generation_metadata.json`:
  ```json
  {
    "source_file": "path/to/original",
    "generation_timestamp": "ISO-8601 timestamp",
    "rows_generated": 25,
    "original_row_count": X,
    "extended_row_count": Y,
    "file_format": "csv|jsonl",
    "sample_size_analyzed": 100,
    "fields_analyzed": ["field1", "field2", ...]
  }
  ```

- Display summary:
  - Original file analyzed
  - Number of rows in original
  - Number of new rows generated
  - Total rows in extended file
  - Output files created
  - Processing time

- Open the output directory: `open DATA_OUTPUT_DIR/<date_time>/`
- When finished, move the `DROPPED_FILE_PATH` into `DROPPED_FILE_PATH_ARCHIVE` directory

## Important Notes

- **CSV Format:** Must have headers in first row, data starts from row 2
- **JSONL Format:** Each line is a complete JSON object, not a JSON array
- **Large Files:** This approach keeps large files out of the agent's context window by:
  - Only reading a sample for analysis
  - Generating to separate files
  - Using bash commands for appending
- **Performance:** Bash append operations are fast and memory-efficient
- **Data Integrity:** The extended file preserves all original data unchanged

## Example Patterns to Recognize

**CSV Example:**
```csv
id,name,email,age,department
1,John Doe,john@example.com,28,Engineering
2,Jane Smith,jane@example.com,32,Marketing
```
→ Generate: Sequential IDs, realistic names, email patterns, age ranges, department categories

**JSONL Example:**
```jsonl
{"user_id": "USR001", "score": 85.5, "tags": ["python", "ml"], "active": true}
{"user_id": "USR002", "score": 92.0, "tags": ["javascript"], "active": false}
```
→ Generate: USR-prefixed IDs, scores in similar range, relevant tags, boolean values

## Special Handling

- **Look for override instructions:** Check if the dropped file contains a comment like `# generate_rows: 50` or `"generate_rows": 50` to override NUM_NEW_ROWS
- **Preserve formatting:** Maintain consistent decimal places, date formats, etc.
- **Handle edge cases:** Empty files, malformed data should be reported gracefully
- **Memory efficiency:** Never load the full extended dataset into memory