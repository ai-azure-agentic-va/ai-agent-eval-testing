#!/usr/bin/env python
"""Load test queries from Golden DataSet sheet."""

import json
import pandas as pd
from pathlib import Path

# Read the Golden DataSet sheet, starting from row 2 (header at row 1)
df = pd.read_excel(
    r'C:\Users\submedip\OneDrive - Publicis Groupe\Documents\Test Queries\VA_Test_Queries_QS.xlsx',
    sheet_name='Golden DataSet',
    header=1,  # Row 1 has headers
    usecols=['#', 'User Question', 'Expected Response', 'Source Document']
)

# Drop rows with missing question numbers
df = df.dropna(subset=['#'])

# Convert to prompt format
prompts = []
skipped_rows = []

for row_num, (_, row) in enumerate(df.iterrows(), start=1):
    # Check if # column is numeric
    try:
        question_num = int(float(row['#']))
    except (ValueError, TypeError):
        # Skip rows with non-numeric # values (e.g., comments/notes)
        skipped_rows.append({
            'row': row_num + 2,  # +2 because we skip the first row and have headers on row 2
            'number_value': str(row['#'])[:50],
            'question': str(row['User Question'])[:50] if pd.notna(row['User Question']) else 'N/A'
        })
        continue

    prompt = {
        "id": f"va-{question_num:03d}",
        "category": "RAG Quality",
        "name": row['User Question'][:50] + "..." if len(str(row['User Question'])) > 50 else str(row['User Question']),
        "query": str(row['User Question']),
        "expected_behavior": str(row['Expected Response']) if pd.notna(row['Expected Response']) else ""
    }

    # Add source document as metadata if available
    if pd.notna(row['Source Document']):
        prompt['source_document'] = str(row['Source Document'])

    prompts.append(prompt)

# Report skipped rows
if skipped_rows:
    print(f"\n[Warning] Skipped {len(skipped_rows)} rows with non-numeric '#' column:")
    for skip in skipped_rows[:10]:  # Show first 10
        print(f"  Row {skip['row']}: # = '{skip['number_value']}' | Question = '{skip['question']}'")
    if len(skipped_rows) > 10:
        print(f"  ... and {len(skipped_rows) - 10} more")

# Ensure output directory exists
output_path = Path('data/test_prompts.json')
output_path.parent.mkdir(parents=True, exist_ok=True)

# Write to JSON file with pretty formatting
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(prompts, f, indent=2, ensure_ascii=False)

print(f"[OK] Loaded {len(prompts)} test queries from Golden DataSet sheet")
print(f"[OK] Saved to {output_path}")
print("\nFirst 5 prompts:")
for p in prompts[:5]:
    print(f"  - {p['id']}: {p['name']}")
