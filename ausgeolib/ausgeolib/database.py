import pandas as pd
from pathlib import Path

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
    
    def get_population(self, area_name, geo_type):
        """
        Get population for a specific area
        
        Parameters:
        -----------
        area_name : str
            Name of the area
        geo_type : str
            Geography type ('sua', 'lga', or 'sa2')
        
        Returns:
        --------
        int or None
            Population value or None if not found
        """
        if geo_type.lower() == 'sua':
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
    
    def get_areas_in_sua(self, sua_name, geo_type, min_overlap=50):
        """
        Get all areas of a specific type within a SUA
        
        Parameters:
        -----------
        sua_name : str
            Name of the Significant Urban Area
        geo_type : str
            Geography type to retrieve ('lga' or 'sa2')
        min_overlap : float, default=50
            Minimum overlap percentage to include
        
        Returns:
        --------
        DataFrame
            DataFrame with areas in the SUA
        """
        # Get SUA code
        sua_file = self.population_dir / "sua_population.csv"
        sua_df = self._load_file(sua_file)
        sua_row = sua_df[sua_df["Significant Urban Area"] == sua_name]
        
        if len(sua_row) == 0:
            raise ValueError(f"SUA not found: {sua_name}")
        
        sua_code = sua_row.iloc[0]["SUA code"]
        
        # Get areas in this SUA
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
    
    def get_sua_for_area(self, area_name, geo_type, min_overlap=50):
        """
        Find which SUA an area belongs to
        
        Parameters:
        -----------
        area_name : str
            Name of the area
        geo_type : str
            Geography type ('lga' or 'sa2')
        min_overlap : float, default=50
            Minimum overlap percentage to include
        
        Returns:
        --------
        DataFrame
            DataFrame with SUAs that contain this area
        """
        if geo_type.lower() == 'lga':
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