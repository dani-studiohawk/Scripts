"""
Utility functions for Australian geographic analysis
Built on top of ausgeolib and GeoHelper
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os
from ausgeolib import GeoDatabase, GeoHelper


def export_to_csv(data, filename, output_dir=None):
    """
    Export DataFrame to CSV file
    
    Parameters:
    -----------
    data : pandas.DataFrame
        DataFrame to export
    filename : str
        Name of the output file (without path)
    output_dir : str, optional
        Directory to save the file (defaults to current directory)
    
    Returns:
    --------
    str
        Path to the saved file
    """
    if output_dir is None:
        output_dir = "."
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Add .csv extension if not present
    if not filename.lower().endswith('.csv'):
        filename += '.csv'
    
    # Full path
    output_path = os.path.join(output_dir, filename)
    
    # Save to CSV
    data.to_csv(output_path, index=False)
    print(f"Data exported to {output_path}")
    
    return output_path


def get_population_by_state():
    """
    Get population breakdown by state
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with state populations
    """
    helper = GeoHelper()
    db = helper.db
    
    try:
        # Get mapping with state information
        mapping = db._load_sal_to_sua()
        
        # Get population data
        pop_data = db._load_sal_population()
        
        # Merge population data with mapping
        merged = mapping.merge(
            pop_data[['SAL_CODE_2021', 'Tot_P_P']], 
            left_on='sal_code', 
            right_on='SAL_CODE_2021',
            how='left'
        )
        
        # Group by state and sum populations
        state_pop = merged.groupby('state')['Tot_P_P'].sum().reset_index()
        state_pop = state_pop.rename(columns={'Tot_P_P': 'population'})
        
        # Sort by population (descending)
        return state_pop.sort_values('population', ascending=False)
    except Exception as e:
        print(f"Error getting state populations: {str(e)}")
        return pd.DataFrame()


def compare_cities(cities, metric='population'):
    """
    Compare multiple cities on a given metric
    
    Parameters:
    -----------
    cities : list
        List of city names to compare
    metric : str, default='population'
        Metric to compare ('population', 'area', 'suburb_count')
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with comparison results
    """
    helper = GeoHelper()
    results = []
    
    for city in cities:
        data = {}
        data['city'] = city
        
        try:
            # Get all suburbs in this city
            suburbs = helper.get_suburbs_in_metropolitan_area(city)
            data['suburb_count'] = len(suburbs)
            
            # Calculate total population if population data is available
            if 'population' in suburbs.columns:
                data['population'] = suburbs['population'].sum()
            
            # Get city area if available
            try:
                sua_file = helper.db.population_dir / "sua_population.csv"
                sua_df = pd.read_csv(sua_file)
                city_row = sua_df[sua_df["Significant Urban Area"] == city]
                
                if len(city_row) > 0 and "Area_sqkm" in city_row.columns:
                    data['area_sqkm'] = city_row.iloc[0]["Area_sqkm"]
                    
                    # Calculate population density if both area and population are available
                    if 'population' in data and 'area_sqkm' in data:
                        data['density'] = data['population'] / data['area_sqkm']
            except:
                pass
            
            results.append(data)
        except Exception as e:
            print(f"Error processing {city}: {str(e)}")
    
    # Create DataFrame from results
    df = pd.DataFrame(results)
    
    # Sort by specified metric
    if metric in df.columns:
        df = df.sort_values(metric, ascending=False)
    
    return df


def find_suburbs_by_name(name_pattern, state=None):
    """
    Find suburbs whose names match a pattern
    
    Parameters:
    -----------
    name_pattern : str
        Pattern to match in suburb names
    state : str, optional
        Filter by state
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with matching suburbs
    """
    helper = GeoHelper()
    db = helper.db
    
    try:
        # Get mapping data
        mapping = db._load_sal_to_sua()
        
        # Filter by name pattern
        matches = mapping[mapping['sal_name'].str.contains(name_pattern, case=False, na=False)]
        
        # Filter by state if specified
        if state is not None:
            matches = matches[matches['state'] == state]
        
        # Add population data if available
        try:
            pop_data = db._load_sal_population()
            matches = matches.merge(
                pop_data[['SAL_CODE_2021', 'Tot_P_P']], 
                left_on='sal_code', 
                right_on='SAL_CODE_2021',
                how='left'
            )
            matches = matches.rename(columns={'Tot_P_P': 'population'})
        except:
            pass
        
        # Sort by state and name
        return matches.sort_values(['state', 'sal_name'])
    except Exception as e:
        print(f"Error finding suburbs: {str(e)}")
        return pd.DataFrame()


def get_suburb_demographics(suburb_code):
    """
    Get detailed demographic breakdown for a suburb
    
    Parameters:
    -----------
    suburb_code : str
        SAL code for the suburb
    
    Returns:
    --------
    dict
        Dictionary with demographic information
    """
    helper = GeoHelper()
    db = helper.db
    
    try:
        # Get demographic data
        demographics = db.get_population_by_demographics(suburb_code, 'sal')
        
        # Get suburb name and other information
        mapping = db._load_sal_to_sua()
        suburb_info = mapping[mapping['sal_code'] == suburb_code]
        
        if len(suburb_info) > 0:
            result = {
                'sal_code': suburb_code,
                'name': suburb_info.iloc[0]['sal_name'],
                'state': suburb_info.iloc[0]['state'],
                'demographics': demographics
            }
            return result
        else:
            return {'demographics': demographics}
    except Exception as e:
        print(f"Error getting demographics: {str(e)}")
        return {}


def export_city_data(city_name, output_dir=None):
    """
    Export comprehensive data for a city to CSV files
    
    Parameters:
    -----------
    city_name : str
        Name of the city to export data for
    output_dir : str, optional
        Directory to save the files (defaults to current directory)
    
    Returns:
    --------
    dict
        Dictionary with paths to exported files
    """
    helper = GeoHelper()
    
    if output_dir is None:
        output_dir = "."
    
    # Create directory for city data
    city_dir = os.path.join(output_dir, f"{city_name.replace(' ', '_')}_data")
    os.makedirs(city_dir, exist_ok=True)
    
    exported_files = {}
    
    try:
        # Get all suburbs in the city
        suburbs = helper.get_suburbs_in_metropolitan_area(city_name)
        
        # Export all suburbs
        all_suburbs_path = export_to_csv(suburbs, "all_suburbs.csv", city_dir)
        exported_files['all_suburbs'] = all_suburbs_path
        
        # Export top 20 largest suburbs
        if 'population' in suburbs.columns:
            largest = suburbs.sort_values('population', ascending=False).head(20)
            largest_path = export_to_csv(largest, "largest_suburbs.csv", city_dir)
            exported_files['largest_suburbs'] = largest_path
        
        # Export suburbs by distance (0-5km, 5-10km, 10-20km, 20+km)
        for dist_range in [(0, 5), (5, 10), (10, 20), (20, 50)]:
            min_dist, max_dist = dist_range
            nearby = helper.get_suburbs_by_distance(city_name, max_dist, sort_by='overlap')
            
            if min_dist > 0:
                nearby = nearby[nearby['distance_km'] >= min_dist]
            
            if len(nearby) > 0:
                range_path = export_to_csv(
                    nearby, 
                    f"suburbs_{min_dist}to{max_dist}km.csv", 
                    city_dir
                )
                exported_files[f'suburbs_{min_dist}to{max_dist}km'] = range_path
        
        return exported_files
    except Exception as e:
        print(f"Error exporting city data: {str(e)}")
        return exported_files





def get_geographic_coverage():
    """
    Calculate how much of each state is covered by SUAs
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with coverage statistics by state
    """
    helper = GeoHelper()
    db = helper.db
    
    try:
        # Get mapping data
        mapping = db._load_sal_to_sua()
        
        # Count SALs by state
        state_counts = mapping.groupby('state')['sal_code'].count().reset_index()
        state_counts = state_counts.rename(columns={'sal_code': 'total_sal_count'})
        
        # Count SALs in urban areas by state
        urban_filter = mapping['sua_name'] != 'Not in any Significant Urban Area'
        urban_counts = mapping[urban_filter].groupby('state')['sal_code'].count().reset_index()
        urban_counts = urban_counts.rename(columns={'sal_code': 'urban_sal_count'})
        
        # Merge counts
        coverage = state_counts.merge(urban_counts, on='state', how='left')
        
        # Calculate coverage percentage
        coverage['urban_percentage'] = (coverage['urban_sal_count'] / coverage['total_sal_count'] * 100).round(1)
        
        # Add population data if available
        try:
            pop_data = db._load_sal_population()
            
            # Merge with mapping to get state information
            pop_with_state = mapping[['sal_code', 'state']].drop_duplicates().merge(
                pop_data[['SAL_CODE_2021', 'Tot_P_P']], 
                left_on='sal_code', 
                right_on='SAL_CODE_2021',
                how='inner'
            )
            
            # Group by state
            state_pop = pop_with_state.groupby('state')['Tot_P_P'].sum().reset_index()
            state_pop = state_pop.rename(columns={'Tot_P_P': 'total_population'})
            
            # Urban population
            urban_pop = pop_with_state[pop_with_state['sal_code'].isin(mapping[urban_filter]['sal_code'])]
            urban_pop = urban_pop.groupby('state')['Tot_P_P'].sum().reset_index()
            urban_pop = urban_pop.rename(columns={'Tot_P_P': 'urban_population'})
            
            # Merge population data
            coverage = coverage.merge(state_pop, on='state', how='left')
            coverage = coverage.merge(urban_pop, on='state', how='left')
            
            # Calculate population percentage
            coverage['urban_pop_percentage'] = (coverage['urban_population'] / coverage['total_population'] * 100).round(1)
        except Exception as e:
            print(f"Warning: Could not calculate population percentages: {str(e)}")
        
        # Sort by urban percentage (descending)
        return coverage.sort_values('urban_percentage', ascending=False)
    except Exception as e:
        print(f"Error calculating geographic coverage: {str(e)}")
        return pd.DataFrame()


# Example usage functions for quick imports
def export_sydney_data(output_dir="."):
    """Export comprehensive data for Sydney"""
    return export_city_data("Sydney", output_dir)

def export_melbourne_data(output_dir="."):
    """Export comprehensive data for Melbourne"""
    return export_city_data("Melbourne", output_dir)

def compare_major_cities(metric='population'):
    """Compare Australia's major cities"""
    major_cities = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"]
    return compare_cities(major_cities, metric)

def find_all_beaches():
    """Find all suburbs containing 'Beach' in their name"""
    return find_suburbs_by_name("Beach")