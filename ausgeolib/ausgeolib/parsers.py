"""
Parsing utilities for special data formats in ausgeolib
"""

import pandas as pd
import re


def parse_sal_population_csv(file_path):
    """
    Parse the SAL population CSV file with merged columns.
    
    Parameters:
    -----------
    file_path : str or Path
        Path to the SAL population CSV file
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with properly separated columns
    """
    # Read the first line to determine the format
    with open(file_path, 'r') as f:
        header_line = f.readline().strip()
    
    # Check if the CSV has column separators or is merged format
    if ',' in header_line:
        # Standard CSV format
        return pd.read_csv(file_path)
    else:
        # Merged column format
        # Define the expected column patterns
        expected_columns = [
            "SAL_CODE_2021", 
            "Tot_P_M", "Tot_P_F", "Tot_P_P"
        ]
        
        # Add age group columns
        age_groups = ["0_4", "5_14", "15_19", "20_24", "25_34", 
                     "35_44", "45_54", "55_64", "65_74", "75_84", "85ov"]
                     
        for age in age_groups:
            expected_columns.extend([
                f"Age_{age}_yr_M", 
                f"Age_{age}_yr_F", 
                f"Age_{age}_yr_P"
            ])
        
        # Read the data
        data = []
        with open(file_path, 'r') as f:
            # Skip header
            next(f)
            for line in f:
                line = line.strip()
                row_data = {}
                
                # Process SAL_CODE_2021 first - look for SAL prefix followed by numbers
                code_match = re.search(r'^SAL(\d+)', line)
                if code_match:
                    sal_code = code_match.group(1)  # Extract just the numeric part
                    row_data["SAL_CODE_2021"] = sal_code
                    line = line[len("SAL" + sal_code):]  # Remove "SAL" + code from the beginning
                
                # Process total population columns
                for col in ["Tot_P_M", "Tot_P_F", "Tot_P_P"]:
                    col_pos = line.find(col)
                    if col_pos >= 0:
                        # Extract next number after column name
                        val_match = re.search(r'{}(\d+)'.format(col), line)
                        if val_match:
                            row_data[col] = int(val_match.group(1))
                            line = line.replace(val_match.group(0), "", 1)
                
                # Process age group columns
                for col in expected_columns[4:]:  # Skip SAL_CODE and total population columns
                    col_pos = line.find(col)
                    if col_pos >= 0:
                        # Extract next number after column name
                        val_match = re.search(r'{}(\d+)'.format(col), line)
                        if val_match:
                            row_data[col] = int(val_match.group(1))
                            line = line.replace(val_match.group(0), "", 1)
                
                data.append(row_data)
        
        # Create DataFrame from parsed data
        return pd.DataFrame(data)