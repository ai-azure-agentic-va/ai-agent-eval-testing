#!/usr/bin/env python
"""
Loader script to convert VA Test Queries Excel file to test_prompts.json format.

Usage:
    python load_va_queries.py --input "VA Test Queries.xlsx" --output data/test_prompts.json
"""

import argparse
import json
import pandas as pd
from pathlib import Path


def load_excel_queries(excel_path, sheet_name='Golden DataSet'):
    """Load test queries from Excel file.

    Args:
        excel_path: Path to the Excel file
        sheet_name: Name of the sheet to read (default: 'Golden DataSet')

    Returns:
        list: List of prompt dictionaries in test_prompts.json format
    """
    # Read Excel file, skipping first row and using row 2 as headers
    df = pd.read_excel(
        excel_path,
        sheet_name=sheet_name,
        header=1,
        names=['Index', 'Number', 'User_Question', 'Expected_Response', 'Source_Document']
    )

    # Drop rows with missing question numbers
    df = df.dropna(subset=['Number'])

    # Convert to prompt format
    prompts = []
    skipped_rows = []

    for row_num, (_, row) in enumerate(df.iterrows(), start=1):
        # Check if Number column is numeric
        try:
            question_num = int(float(row['Number']))
        except (ValueError, TypeError):
            # Skip rows with non-numeric Number values (e.g., comments/notes)
            skipped_rows.append({
                'row': row_num + 2,  # +2 because we skip the first row and have headers on row 2
                'number_value': str(row['Number'])[:50],
                'question': str(row['User_Question'])[:50] if pd.notna(row['User_Question']) else 'N/A'
            })
            continue

        prompt = {
            "id": f"va-{question_num:03d}",
            "category": "RAG Quality",
            "name": row['User_Question'][:50] + "..." if len(row['User_Question']) > 50 else row['User_Question'],
            "query": row['User_Question'],
            "expected_behavior": row['Expected_Response']
        }

        # Add source document as metadata if available
        if pd.notna(row['Source_Document']):
            prompt['source_document'] = row['Source_Document']

        prompts.append(prompt)

    # Report skipped rows
    if skipped_rows:
        print(f"\nWarning: Skipped {len(skipped_rows)} rows with non-numeric '#' column:")
        for skip in skipped_rows[:10]:  # Show first 10
            print(f"  Row {skip['row']}: # = '{skip['number_value']}' | Question = '{skip['question']}'")
        if len(skipped_rows) > 10:
            print(f"  ... and {len(skipped_rows) - 10} more")

    return prompts


def save_prompts(prompts, output_path, mode='replace'):
    """Save prompts to JSON file.

    Args:
        prompts: List of prompt dictionaries
        output_path: Path to output JSON file
        mode: 'replace' to overwrite, 'merge' to combine with existing prompts
    """
    output_path = Path(output_path)

    if mode == 'merge' and output_path.exists():
        # Load existing prompts
        with open(output_path, 'r') as f:
            existing_prompts = json.load(f)

        # Get existing IDs
        existing_ids = {p['id'] for p in existing_prompts}

        # Add new prompts that don't already exist
        for prompt in prompts:
            if prompt['id'] not in existing_ids:
                existing_prompts.append(prompt)
                print(f"Added: {prompt['id']} - {prompt['name']}")
            else:
                print(f"Skipped (already exists): {prompt['id']} - {prompt['name']}")

        prompts = existing_prompts

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON file with pretty formatting
    with open(output_path, 'w') as f:
        json.dump(prompts, f, indent=2)

    print(f"\nSaved {len(prompts)} prompts to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert VA Test Queries Excel to test_prompts.json format"
    )
    parser.add_argument(
        '--input',
        default='VA Test Queries.xlsx',
        help='Path to input Excel file (default: VA Test Queries.xlsx)'
    )
    parser.add_argument(
        '--output',
        default='data/test_prompts.json',
        help='Path to output JSON file (default: data/test_prompts.json)'
    )
    parser.add_argument(
        '--mode',
        choices=['replace', 'merge'],
        default='replace',
        help='replace=overwrite output file, merge=add to existing prompts (default: replace)'
    )
    parser.add_argument(
        '--sheet',
        default='Golden DataSet',
        help='Sheet name to read from Excel file (default: Golden DataSet)'
    )

    args = parser.parse_args()

    # Validate input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    print(f"Loading queries from {args.input} (sheet: {args.sheet})...")
    prompts = load_excel_queries(args.input, sheet_name=args.sheet)

    print(f"\nLoaded {len(prompts)} queries:")
    for prompt in prompts:
        try:
            print(f"  - {prompt['id']}: {prompt['name']}")
        except UnicodeEncodeError:
            # Handle Windows console encoding issues
            safe_name = prompt['name'].encode('ascii', errors='replace').decode()
            print(f"  - {prompt['id']}: {safe_name}")

    print(f"\nSaving to {args.output} (mode: {args.mode})...")
    save_prompts(prompts, args.output, mode=args.mode)

    print("\nDone!")
    return 0


if __name__ == '__main__':
    exit(main())
