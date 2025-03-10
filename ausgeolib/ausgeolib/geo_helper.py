"""
High-level convenience functions for Australian geographic analysis
Build on top of ausgeolib to provide easy-to-use natural language-like queries
"""

import pandas as pd
import numpy as np
from ausgeolib import GeoDatabase
from pathlib import Path


class GeoHelper:
    def __init__(self, data_dir=r"G:\My Drive\Workflow\Resources\Geolocation Files"):
        """Initialize the GeoHelper with an underlying GeoDatabase instance"""
        self.db = GeoDatabase(data_dir)
        
    def get_suburbs_in_metropolitan_area(self, city_name, min_overlap=50):
        """
        Get all suburbs (SAL areas) within a metropolitan area
        
        Parameters:
        -----------
        city_name : str
            Name of the metropolitan area (SUA)
        min_overlap : float, default=50
            Minimum percentage overlap required to consider a suburb part of the city
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with suburb information sorted by population (descending) if available
        """
        # Get all SAL areas in the specified SUA
        suburbs = self.db.get_areas_in_sua(city_name, 'sal', min_overlap=min_overlap)
        
        if len(suburbs) == 0:
            print(f"No suburbs found in {city_name}")
            return pd.DataFrame()
            
        # Sort by population if available, otherwise by name
        if 'population' in suburbs.columns and not suburbs['population'].isna().all():
            return suburbs.sort_values('population', ascending=False)
        else:
            # Fall back to sorting by name if population isn't available
            return suburbs.sort_values('sal_name')
    
    def get_major_metropolitan_areas(self, min_population=100000):
        """
        Get a list of major metropolitan areas (SUAs) by population
        
        Parameters:
        -----------
        min_population : int, default=100000
            Minimum population to be considered a major metropolitan area
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with metropolitan areas and their populations
        """
        try:
            # Load SUA population data
            sua_file = self.db.population_dir / "sua_population.csv"
            sua_df = pd.read_csv(sua_file)
            
            # Filter by minimum population
            major_cities = sua_df[sua_df["Population"] >= min_population]
            
            # Return sorted by population (high to low)
            return major_cities.sort_values("Population", ascending=False)
        except Exception as e:
            print(f"Error getting metropolitan areas: {str(e)}")
            return pd.DataFrame()
    
    def get_suburbs_by_distance(self, city_name, max_distance_km=20, sort_by='population'):
        """
        Get suburbs within a certain distance from a metropolitan area's center
        
        Note: This is an approximation as we don't have the exact coordinates.
        It uses the fact that suburbs with higher overlap percentage are typically closer to the center.
        
        Parameters:
        -----------
        city_name : str
            Name of the metropolitan area (SUA)
        max_distance_km : float, default=20
            Approximate maximum distance from city center in kilometers
        sort_by : str, default='population'
            Sort criterion ('population', 'distance', 'overlap', or 'name')
                
        Returns:
        --------
        pandas.DataFrame
            DataFrame with suburbs sorted by the specified criterion
        """
        # Get all suburbs in the city
        all_suburbs = self.db.get_areas_in_sua(city_name, 'sal', min_overlap=1)
        
        if len(all_suburbs) == 0:
            print(f"No suburbs found in {city_name}")
            return pd.DataFrame()
        
        # Always make a copy to avoid SettingWithCopyWarning
        suburbs = all_suburbs.copy()
        
        # Add population data if needed and possible
        if 'population' not in suburbs.columns:
            try:
                suburbs = self._add_population_data(suburbs, 'sal_code')
            except Exception as e:
                print(f"Could not add population data: {str(e)}")
                # Continue without population data
        
        # Filter suburbs based on approximate distance
        try:
            # Get city area in square kilometers (from SUA data)
            sua_file = self.db.population_dir / "sua_population.csv"
            sua_df = pd.read_csv(sua_file)
            city_row = sua_df[sua_df["Significant Urban Area"] == city_name]
            
            if len(city_row) > 0 and "Area_sqkm" in city_row.columns:
                city_area = city_row.iloc[0]["Area_sqkm"]
                
                # Estimate city radius (assuming circular shape)
                city_radius = np.sqrt(city_area / np.pi)
                
                # Estimate suburb distance based on overlap percentage
                # Higher overlap = closer to center (rough approximation)
                suburbs.loc[:, 'distance_km'] = city_radius * (1 - (suburbs['overlap_pct'] / 100))
                
                # Filter by max distance
                distance_filter = suburbs['distance_km'] <= max_distance_km
                suburbs = suburbs[distance_filter].copy()  # Create a copy for the filtered result
            else:
                # If we can't calculate distance, use overlap as a proxy
                # Higher overlap = closer to center
                threshold = 100 - (max_distance_km * 5)  # Rough conversion
                threshold = max(1, threshold)  # Ensure minimum 1% overlap
                
                overlap_filter = suburbs['overlap_pct'] >= threshold
                suburbs = suburbs[overlap_filter].copy()  # Create a copy for the filtered result
                suburbs.loc[:, 'distance_km'] = 100 - suburbs['overlap_pct']  # Rough estimate
        except Exception as e:
            print(f"Warning: Could not calculate distances: {str(e)}")
            # Fall back to just returning all suburbs
            suburbs.loc[:, 'distance_km'] = np.nan
        
        # Sort based on specified criterion
        if sort_by.lower() == 'population' and 'population' in suburbs.columns and not suburbs['population'].isna().all():
            return suburbs.sort_values('population', ascending=False)
        elif sort_by.lower() == 'distance' and 'distance_km' in suburbs.columns:
            return suburbs.sort_values('distance_km')
        elif sort_by.lower() == 'overlap':
            return suburbs.sort_values('overlap_pct', ascending=False)
        elif sort_by.lower() == 'name':
            return suburbs.sort_values('sal_name')
        else:
            # Default sort by overlap percentage (best proxy for proximity to city center)
            return suburbs.sort_values('overlap_pct', ascending=False)
    
    def get_largest_suburbs(self, n=10, state=None):
        """
        Get the largest suburbs by population
        
        Parameters:
        -----------
        n : int, default=10
            Number of suburbs to return
        state : str, optional
            Filter by state ('New South Wales', 'Victoria', etc.)
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with the largest suburbs
        """
        try:
            # Load all SAL population data
            sal_data = self.db._load_sal_population()
            
            # Filter by state if specified
            if state and 'state' in sal_data.columns:
                sal_data = sal_data[sal_data['state'] == state]
            
            # Ensure we have the population column
            if 'Tot_P_P' in sal_data.columns:
                # Sort by population and get top N
                largest = sal_data.sort_values('Tot_P_P', ascending=False).head(n)
                
                # Rename for clarity
                if 'SAL_CODE_2021' in largest.columns:
                    largest = largest.rename(columns={
                        'SAL_CODE_2021': 'sal_code',
                        'Tot_P_P': 'population'
                    })
                
                return largest
            else:
                print("Population data not available")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error getting largest suburbs: {str(e)}")
            return pd.DataFrame()
    
    def get_all_suburbs_in_state(self, state, min_population=None):
        """
        Get all suburbs in a specific state
        
        Parameters:
        -----------
        state : str
            State name ('New South Wales', 'Victoria', etc.)
        min_population : int, optional
            Minimum population to include
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with all suburbs in the state
        """
        try:
            # Load SAL to SUA mapping which has state information
            mapping = self.db._load_sal_to_sua()
            
            # Filter by state
            state_suburbs = mapping[mapping['state'] == state].drop_duplicates('sal_code')
            
            # Add population data
            state_suburbs = self._add_population_data(state_suburbs, 'sal_code')
            
            # Filter by minimum population if specified
            if min_population is not None and 'population' in state_suburbs.columns:
                state_suburbs = state_suburbs[state_suburbs['population'] >= min_population]
            
            # Sort by population (high to low)
            return state_suburbs.sort_values('population', ascending=False)
        except Exception as e:
            print(f"Error getting suburbs in state: {str(e)}")
            return pd.DataFrame()
    
    def find_similar_suburbs(self, suburb_name, n=5):
        """
        Find suburbs with similar demographic profiles
        
        Parameters:
        -----------
        suburb_name : str
            Name of the reference suburb
        n : int, default=5
            Number of similar suburbs to return
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with similar suburbs
        """
        # TODO: Implement similarity calculation based on demographics
        # This would require demographic data which we partially have
        pass
    
    def _add_population_data(self, df, code_column):
        """Helper method to add population data to a DataFrame"""
        try:
            sal_population = self.db._load_sal_population()
            
            # First check the data types and convert if needed
            if df[code_column].dtype != sal_population['SAL_CODE_2021'].dtype:
                # Try to make types compatible
                if df[code_column].dtype == 'object' and sal_population['SAL_CODE_2021'].dtype == 'int64':
                    # Try to convert strings to integers
                    try:
                        df[code_column] = df[code_column].astype(str).str.replace('SAL', '')
                        df[code_column] = pd.to_numeric(df[code_column], errors='coerce')
                    except:
                        pass
                elif df[code_column].dtype == 'int64' and sal_population['SAL_CODE_2021'].dtype == 'object':
                    # Try to convert integers to strings
                    try:
                        df[code_column] = df[code_column].astype(str)
                    except:
                        pass
            
            # Try direct merge
            merge_result = df.merge(
                sal_population[['SAL_CODE_2021', 'Tot_P_P']], 
                left_on=code_column, 
                right_on='SAL_CODE_2021',
                how='left'
            )
            
            # Rename for clarity and drop temporary columns
            result = merge_result.rename(columns={'Tot_P_P': 'population'})
            
            return result
        except Exception as e:
            print(f"Warning: Could not add population data: {str(e)}")
            return df


# Example usage functions
def suburbs_in_city(city_name):
    """Get all suburbs in a major city, sorted by population"""
    helper = GeoHelper()
    return helper.get_suburbs_in_metropolitan_area(city_name)

def suburbs_near_city(city_name, distance_km=20):
    """Get suburbs within specified kilometers of a major city"""
    helper = GeoHelper()
    return helper.get_suburbs_by_distance(city_name, distance_km)

def largest_suburbs(n=10, state=None):
    """Get the largest suburbs by population"""
    helper = GeoHelper()
    return helper.get_largest_suburbs(n, state)

def major_cities(min_population=100000):
    """Get list of major cities by population"""
    helper = GeoHelper()
    return helper.get_major_metropolitan_areas(min_population)


if __name__ == "__main__":
    # Example demonstrating usage
    helper = GeoHelper()
    
    print("\n=== Major Metropolitan Areas ===")
    cities = helper.get_major_metropolitan_areas()
    print(cities[["Significant Urban Area", "Population"]].head())
    
    print("\n=== Largest Suburbs in Australia ===")
    largest = helper.get_largest_suburbs(5)
    print(largest[["sal_code", "population"]].head())
    
    print("\n=== Suburbs in Sydney ===")
    sydney_suburbs = helper.get_suburbs_in_metropolitan_area("Sydney")
    print(sydney_suburbs[["sal_name", "population"]].head())
    
    print("\n=== Suburbs within 15km of Melbourne ===")
    melbourne_nearby = helper.get_suburbs_by_distance("Melbourne", 15)
    print(melbourne_nearby[["sal_name", "population", "distance_km"]].head())