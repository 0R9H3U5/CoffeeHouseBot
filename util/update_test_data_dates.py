#!/usr/bin/env python3
"""
Script to update the dates in populate-test-data.sql to be relative to the current date.
This ensures the test data remains useful for testing without manual modifications.
"""

import os
import re
import datetime
import argparse
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Update dates in populate-test-data.sql')
    parser.add_argument('--sql-dir', type=str, default='../sql',
                        help='Directory containing the SQL files (default: ../sql)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file path (default: overwrite the original file)')
    return parser.parse_args()

def update_dates(sql_content, base_date=None):
    """
    Update all dates in the SQL content to be relative to the base_date.
    
    Args:
        sql_content (str): The SQL content to update
        base_date (datetime.datetime, optional): The base date to use. Defaults to current date.
    
    Returns:
        str: The updated SQL content
    """
    if base_date is None:
        base_date = datetime.datetime.now()
    
    # Define date patterns to match
    date_patterns = [
        # Pattern for 'YYYY-MM-DD HH:MM:SS'
        (r"'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'", 
         lambda m: f"'{base_date.strftime('%Y-%m-%d %H:%M:%S')}'"),
        
        # Pattern for 'YYYY-MM-DD'
        (r"'(\d{4}-\d{2}-\d{2})'", 
         lambda m: f"'{base_date.strftime('%Y-%m-%d')}'"),
        
        # Pattern for CURRENT_TIMESTAMP - INTERVAL 'X days'
        (r"CURRENT_TIMESTAMP - INTERVAL '(\d+) days'", 
         lambda m: f"CURRENT_TIMESTAMP - INTERVAL '{m.group(1)} days'"),
        
        # Pattern for CURRENT_TIMESTAMP + INTERVAL 'X days'
        (r"CURRENT_TIMESTAMP \+ INTERVAL '(\d+) days'", 
         lambda m: f"CURRENT_TIMESTAMP + INTERVAL '{m.group(1)} days'")
    ]
    
    # Apply each pattern
    updated_content = sql_content
    for pattern, replacement in date_patterns:
        updated_content = re.sub(pattern, replacement, updated_content)
    
    return updated_content

def main():
    """Main function to update the SQL file."""
    args = parse_args()
    
    # Determine the SQL file path
    sql_dir = Path(args.sql_dir)
    sql_file = sql_dir / 'populate-test-data.sql'
    
    # Check if the file exists
    if not sql_file.exists():
        print(f"Error: SQL file not found at {sql_file}")
        return 1
    
    # Read the SQL file
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Update the dates
    updated_content = update_dates(sql_content)
    
    # Determine the output file path
    output_file = args.output if args.output else sql_file
    
    # Write the updated content
    with open(output_file, 'w') as f:
        f.write(updated_content)
    
    print(f"Successfully updated dates in {output_file}")
    return 0

if __name__ == "__main__":
    exit(main()) 