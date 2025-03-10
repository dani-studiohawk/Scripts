import pandas as pd
from pathlib import Path
from .parsers import parse_sal_population_csv

class GeoDatabase:
    def __init__(self, data_dir=r"G:\My Drive\Workflow\Resources\Geolocation Files"):
        """
        Initialize the database with paths to data files
        
        Parameters:
        -----------
        data_dir : str
            Path to the directory containing Population and Relationships folders
        """
        self.data_dir = Path(data_dir)
        self.population_dir = self.data_dir / "Population"
        self.relationships_dir = self.data_dir / "Relationships"
        
        # Cache for loaded data
        self._cache = {}
    
    def _load_file(self, file_path):
        """Load a CSV file with caching"""
        file_path = Path(file_path)
        if file_path in self._cache:
            return self._cache[file_path]
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        data = pd.read_csv(file_path)
        self._cache[file_path] = data
        return data
    
    def _load_sal_population(self):
        """Load SAL population data with special parsing."""
        if 'sal_population' not in self._cache:
            file_path = self.population_dir / 'sal_population.csv'
            if file_path.exists():
                self._cache['sal_population'] = parse_sal_population_csv(file_path)
            else:
                raise FileNotFoundError(f"SAL population file not found: {file_path}")
        return self._cache['sal_population']

    def _load_sal_to_sua(self):
        """Load SAL to SUA mapping."""
        if 'sal_to_sua' not in self._cache:
            file_path = self.relationships_dir / 'sal_to_sua.csv'
            if file_path.exists():
                self._cache['sal_to_sua'] = pd.read_csv(file_path)
            else:
                raise FileNotFoundError(f"SAL to SUA mapping file not found: {file_path}")
        return self._cache['sal_to_sua']
    
    def get_population(self, area_name, geo_type):
        """
        Get population for a specific area
        
        Parameters:
        -----------
        area_name : str
            Name of the area
        geo_type : str
            Geography type ('sua', 'lga', 'sa2', or 'sal')
        
        Returns:
        --------
        int or None
            Population value or None if not found
        """
        # Handle SAL areas
        if geo_type.lower() == 'sal':
            sal_data = self._load_sal_population()
            
            # Try to match by code if area_name is numeric
            if area_name.isdigit():
                # Try with and without SAL prefix
                result = sal_data[sal_data['SAL_CODE_2021'] == area_name]
                
                if len(result) == 0:
                    # Try with SAL prefix
                    result = sal_data[sal_data['SAL_CODE_2021'] == f"SAL{area_name}"]
            elif area_name.startswith('SAL') and area_name[3:].isdigit():
                # If area_name already has SAL prefix
                result = sal_data[sal_data['SAL_CODE_2021'] == area_name]
                
                if len(result) == 0:
                    # Try without prefix
                    result = sal_data[sal_data['SAL_CODE_2021'] == area_name[3:]]
            else:
                # Add SAL name lookup if needed
                raise ValueError(f"SAL lookup by name not implemented. Use SAL code instead.")
            
            if len(result) == 0:
                raise ValueError(f"SAL area not found: {area_name}")
            
            # Return total population
            return result.iloc[0]['Tot_P_P']
        
        # Original implementation for other geo types
        elif geo_type.lower() == 'sua':
            file_path = self.population_dir / "sua_population.csv"
            df = self._load_file(file_path)
            result = df[df["Significant Urban Area"] == area_name]
            if len(result) > 0:
                return result.iloc[0]["Population"]
        
        elif geo_type.lower() == 'lga':
            file_path = self.population_dir / "lga_population.csv"
            df = self._load_file(file_path)
            result = df[df["Local Government Area"] == area_name]
            if len(result) > 0:
                return result.iloc[0]["population"]
        
        return None
    
    def get_population_by_demographics(self, area_name, geo_type, age_group=None, gender=None):
        """
        Get population breakdown by demographics.
        
        Parameters:
        -----------
        area_name : str
            Name or code of the area
        geo_type : str
            Geography type ('sal', 'lga', 'sua', etc.)
        age_group : str, optional
            Age group to filter by (e.g., '0_4', '25_34', or 'total')
        gender : str, optional
            Gender to filter by ('M', 'F', or None for total)
            
        Returns:
        --------
        int or dict
            Population value or dictionary of demographic breakdowns
        """
        if geo_type.lower() != 'sal':
            raise ValueError(f"Demographic breakdown only supported for SAL areas currently")
        
        sal_data = self._load_sal_population()
        
        # Find the area with SAL prefix handling
        if area_name.isdigit():
            # Try with and without SAL prefix
            result = sal_data[sal_data['SAL_CODE_2021'] == area_name]
            
            if len(result) == 0:
                # Try with SAL prefix
                result = sal_data[sal_data['SAL_CODE_2021'] == f"SAL{area_name}"]
        elif area_name.startswith('SAL') and area_name[3:].isdigit():
            # If area_name already has SAL prefix
            result = sal_data[sal_data['SAL_CODE_2021'] == area_name]
            
            if len(result) == 0:
                # Try without prefix
                result = sal_data[sal_data['SAL_CODE_2021'] == area_name[3:]]
        else:
            raise ValueError(f"SAL lookup by name not implemented. Use SAL code instead.")
        
        if len(result) == 0:
            raise ValueError(f"SAL area not found: {area_name}")
        
        row = result.iloc[0]
        
        # Return specific demographic if requested
        if age_group and gender:
            if age_group == 'total':
                col = f"Tot_P_{'M' if gender.upper() == 'M' else 'F'}"
            else:
                col = f"Age_{age_group}_yr_{'M' if gender.upper() == 'M' else 'F'}"
            
            if col in row:
                return row[col]
            else:
                raise ValueError(f"Demographic column not found: {col}")
        
        # Return all demographics if no specific filter
        if not age_group and not gender:
            demographics = {
                'total': {
                    'total': row['Tot_P_P'],
                    'male': row['Tot_P_M'],
                    'female': row['Tot_P_F']
                }
            }
            
            # Add all age groups
            age_groups = ["0_4", "5_14", "15_19", "20_24", "25_34", 
                         "35_44", "45_54", "55_64", "65_74", "75_84", "85ov"]
            
            for age in age_groups:
                demographics[age] = {
                    'total': row[f"Age_{age}_yr_P"],
                    'male': row[f"Age_{age}_yr_M"],
                    'female': row[f"Age_{age}_yr_F"]
                }
            
            return demographics
        
        # Return specific age group with all genders
        if age_group and not gender:
            if age_group == 'total':
                return {
                    'total': row['Tot_P_P'],
                    'male': row['Tot_P_M'],
                    'female': row['Tot_P_F']
                }
            else:
                return {
                    'total': row[f"Age_{age_group}_yr_P"],
                    'male': row[f"Age_{age_group}_yr_M"],
                    'female': row[f"Age_{age_group}_yr_F"]
                }
        
        # Return all age groups for specific gender
        if not age_group and gender:
            gender_key = 'M' if gender.upper() == 'M' else 'F'
            demographics = {
                'total': row[f"Tot_P_{gender_key}"]
            }
            
            age_groups = ["0_4", "5_14", "15_19", "20_24", "25_34", 
                         "35_44", "45_54", "55_64", "65_74", "75_84", "85ov"]
            
            for age in age_groups:
                demographics[age] = row[f"Age_{age}_yr_{gender_key}"]
            
            return demographics
    
    def get_areas_in_sua(self, sua_name, geo_type, min_overlap=50):
        """
        Get all areas of a specific type within a SUA
        
        Parameters:
        -----------
        sua_name : str
            Name of the Significant Urban Area
        geo_type : str
            Geography type to retrieve ('lga', 'sa2', or 'sal')
        min_overlap : float, default=50
            Minimum overlap percentage to include
        
        Returns:
        --------
        DataFrame
            DataFrame with areas in the SUA
        """
        # Handle SAL areas
        if geo_type.lower() == 'sal':
            # Load SAL to SUA mapping directly (skip SUA code lookup)
            try:
                mapping = self._load_sal_to_sua()
                
                # Filter by SUA name and minimum overlap directly
                result = mapping[(mapping['sua_name'] == sua_name) & 
                                (mapping['overlap_pct'] >= min_overlap)]
                
                if len(result) == 0:
                    print(f"No areas found for SUA '{sua_name}' with min overlap {min_overlap}%")
                    # Try case-insensitive search
                    result = mapping[mapping['sua_name'].str.lower() == sua_name.lower()]
                    if len(result) > 0:
                        print(f"Found matches with case-insensitive search. Did you mean '{result['sua_name'].iloc[0]}'?")
                    return pd.DataFrame()
                
                # Optionally, add population data if available
                try:
                    sal_population = self._load_sal_population()
                    
                    # Try various ways to match up the SAL codes
                    # First try direct match
                    merged = result.merge(
                        sal_population[['SAL_CODE_2021', 'Tot_P_P']], 
                        left_on='sal_code', 
                        right_on='SAL_CODE_2021',
                        how='left'
                    )
                    
                    # If that didn't work, try with prefix
                    if 'Tot_P_P' in merged.columns and merged['Tot_P_P'].isna().all():
                        # Try with SAL prefix
                        result_with_prefix = result.copy()
                        result_with_prefix['sal_code_with_prefix'] = 'SAL' + result['sal_code'].astype(str)
                        merged = result_with_prefix.merge(
                            sal_population[['SAL_CODE_2021', 'Tot_P_P']], 
                            left_on='sal_code_with_prefix', 
                            right_on='SAL_CODE_2021',
                            how='left'
                        )
                        merged = merged.drop('sal_code_with_prefix', axis=1)
                    
                    # Rename for consistency
                    if 'Tot_P_P' in merged.columns:
                        merged = merged.rename(columns={'Tot_P_P': 'population'})
                        result = merged
                except Exception as e:
                    print(f"Warning: Could not add population data: {str(e)}")
                
                return result
            except Exception as e:
                print(f"Error in get_areas_in_sua for SAL: {str(e)}")
                return pd.DataFrame()
        
        # Get areas in this SUA (original implementation for other geo types)
        else:
            try:
                # Get SUA code
                sua_file = self.population_dir / "sua_population.csv"
                sua_df = self._load_file(sua_file)
                sua_row = sua_df[sua_df["Significant Urban Area"] == sua_name]
                
                if len(sua_row) == 0:
                    raise ValueError(f"SUA not found: {sua_name}")
                
                sua_code = sua_row.iloc[0]["SUA code"]
                
                if geo_type.lower() == 'lga':
                    rel_file = self.relationships_dir / "lga_to_sua.csv"
                    rel_df = self._load_file(rel_file)
                    
                    # Filter for this SUA and minimum overlap
                    result = rel_df[
                        (rel_df["sua_code"] == sua_code) & 
                        (rel_df["overlap_percentage"] >= min_overlap)
                    ]
                    
                    # Add population data if available
                    try:
                        pop_file = self.population_dir / "lga_population.csv"
                        pop_df = self._load_file(pop_file)
                        result = result.merge(
                            pop_df,
                            left_on="lga_code",
                            right_on="LGA code",
                            how="left"
                        )
                    except:
                        pass
                    
                    return result
                
                elif geo_type.lower() == 'sa2':
                    rel_file = self.relationships_dir / "sa2_to_sua.csv"
                    rel_df = self._load_file(rel_file)
                    
                    # Filter for this SUA and minimum overlap
                    result = rel_df[
                        (rel_df["sua_code"] == sua_code) & 
                        (rel_df["overlap_percentage"] >= min_overlap)
                    ]
                    
                    return result
                
                raise ValueError(f"Invalid geography type: {geo_type}")
            except Exception as e:
                print(f"Error in get_areas_in_sua: {str(e)}")
                return pd.DataFrame()
    
    def get_sua_for_area(self, area_name, geo_type, min_overlap=50):
        """
        Find which SUA an area belongs to
        
        Parameters:
        -----------
        area_name : str
            Name of the area
        geo_type : str
            Geography type ('lga', 'sa2', or 'sal')
        min_overlap : float, default=50
            Minimum overlap percentage to include
        
        Returns:
        --------
        DataFrame
            DataFrame with SUAs that contain this area
        """
        # Handle SAL areas
        if geo_type.lower() == 'sal':
            # Load SAL to SUA mapping
            mapping = self._load_sal_to_sua()
            
            # Handle different SAL code formats
            if area_name.isdigit():
                # Try without prefix first
                result = mapping[(mapping['sal_code'] == area_name) & 
                                (mapping['overlap_pct'] >= min_overlap)]
                
                if len(result) == 0:
                    # Try with SAL prefix
                    result = mapping[(mapping['sal_code'] == f"SAL{area_name}") & 
                                    (mapping['overlap_pct'] >= min_overlap)]
            elif area_name.startswith('SAL') and area_name[3:].isdigit():
                # Has SAL prefix already
                result = mapping[(mapping['sal_code'] == area_name) & 
                                (mapping['overlap_pct'] >= min_overlap)]
                
                if len(result) == 0:
                    # Try without prefix
                    result = mapping[(mapping['sal_code'] == area_name[3:]) & 
                                    (mapping['overlap_pct'] >= min_overlap)]
            else:
                # Filter by SAL name and minimum overlap
                result = mapping[(mapping['sal_name'] == area_name) & 
                                (mapping['overlap_pct'] >= min_overlap)]
            
            if len(result) == 0:
                return pd.DataFrame()  # No matching SUAs
            
            # Add SUA population data if available
            try:
                sua_file = self.population_dir / "sua_population.csv"
                sua_df = self._load_file(sua_file)
                result = result.merge(
                    sua_df,
                    left_on="sua_code",
                    right_on="SUA code",
                    how="left"
                )
            except:
                pass
            
            # Return SUAs sorted by overlap percentage (highest first)
            return result.sort_values('overlap_pct', ascending=False)
        
        # Original implementation for other geo types
        elif geo_type.lower() == 'lga':
            # Get LGA code
            pop_file = self.population_dir / "lga_population.csv"
            pop_df = self._load_file(pop_file)
            area_row = pop_df[pop_df["Local Government Area"] == area_name]
            
            if len(area_row) == 0:
                raise ValueError(f"LGA not found: {area_name}")
            
            area_code = area_row.iloc[0]["LGA code"]
            
            # Get SUAs for this LGA
            rel_file = self.relationships_dir / "lga_to_sua.csv"
            rel_df = self._load_file(rel_file)
            
            # Filter for this LGA and minimum overlap
            result = rel_df[
                (rel_df["lga_code"] == area_code) & 
                (rel_df["overlap_percentage"] >= min_overlap)
            ]
            
            # Add population data if available
            try:
                sua_file = self.population_dir / "sua_population.csv"
                sua_df = self._load_file(sua_file)
                result = result.merge(
                    sua_df,
                    left_on="sua_code",
                    right_on="SUA code",
                    how="left"
                )
            except:
                pass
            
            return result
        
        elif geo_type.lower() == 'sa2':
            # Get SA2 code
            rel_file = self.relationships_dir / "sa2_to_sua.csv"
            rel_df = self._load_file(rel_file)
            area_rows = rel_df[rel_df["sa2_name"] == area_name]
            
            if len(area_rows) == 0:
                raise ValueError(f"SA2 not found: {area_name}")
            
            area_code = area_rows.iloc[0]["sa2_code"]
            
            # Filter for this SA2 and minimum overlap
            result = rel_df[
                (rel_df["sa2_code"] == area_code) & 
                (rel_df["overlap_percentage"] >= min_overlap)
            ]
            
            # Add population data if available
            try:
                sua_file = self.population_dir / "sua_population.csv"
                sua_df = self._load_file(sua_file)
                result = result.merge(
                    sua_df,
                    left_on="sua_code",
                    right_on="SUA code",
                    how="left"
                )
            except:
                pass
            
            return result
        
        raise ValueError(f"Invalid geography type: {geo_type}")