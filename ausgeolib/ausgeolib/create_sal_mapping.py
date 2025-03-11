"""
Script to create spatial relationship mapping between SAL and SUA areas
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import os
import sys
import time


def create_sal_to_sua_mapping(data_dir, output_file=None):
    """
    Create mapping between SAL and SUA areas.
    
    Parameters:
    -----------
    data_dir : str or Path
        Path to the data directory containing Boundaries folder
    output_file : str or Path, optional
        Path to save the resulting CSV mapping (defaults to 'Relationships/sal_to_sua.csv')
        
    Returns:
    --------
    str
        Path to the generated mapping file
    """
    data_dir = Path(data_dir)
    
    # Define file paths
    sal_shapefile = data_dir / 'Boundaries' / 'SAL_2021_AUST_GDA2020_SHP' / 'SAL_2021_AUST_GDA2020.shp'
    sua_shapefile = data_dir / 'Boundaries' / 'SUA_2021_AUST_GDA2020' / 'SUA_2021_AUST_GDA2020.shp'
    
    if output_file is None:
        output_file = data_dir / 'Relationships' / 'sal_to_sua.csv'
    else:
        output_file = Path(output_file)
    
    # Check if mapping already exists
    if output_file.exists():
        print(f"SAL to SUA mapping already exists: {output_file}")
        return str(output_file)
    
    # Check if shapefiles exist
    if not sal_shapefile.exists():
        raise FileNotFoundError(f"SAL shapefile not found: {sal_shapefile}")
    
    if not sua_shapefile.exists():
        raise FileNotFoundError(f"SUA shapefile not found: {sua_shapefile}")
    
    # Create relationships directory if needed
    os.makedirs(output_file.parent, exist_ok=True)
    
    # Load shapefiles
    print(f"Loading SAL shapefile...")
    start_time = time.time()
    try:
        sal_gdf = gpd.read_file(sal_shapefile)
        print(f"Loaded {len(sal_gdf)} SAL areas in {time.time() - start_time:.2f} seconds")
        
        # Check for None geometries
        none_geoms = sal_gdf[sal_gdf.geometry.isna()]
        if len(none_geoms) > 0:
            print(f"Warning: Found {len(none_geoms)} SAL areas with None geometries")
            # Print first few examples
            for i, row in none_geoms.head(5).iterrows():
                print(f"  SAL with None geometry: Code={row.get('SAL_CODE21', 'Unknown')}, Name={row.get('SAL_NAME21', 'Unknown')}")
        
    except Exception as e:
        print(f"Error loading SAL shapefile: {str(e)}")
        raise
    
    print(f"Loading SUA shapefile...")
    start_time = time.time()
    try:
        sua_gdf = gpd.read_file(sua_shapefile)
        print(f"Loaded {len(sua_gdf)} SUA areas in {time.time() - start_time:.2f} seconds")
        
        # Check for None geometries
        none_geoms = sua_gdf[sua_gdf.geometry.isna()]
        if len(none_geoms) > 0:
            print(f"Warning: Found {len(none_geoms)} SUA areas with None geometries")
            # Print first few examples
            for i, row in none_geoms.head(5).iterrows():
                print(f"  SUA with None geometry: Code={row.get('SUA_CODE21', 'Unknown')}, Name={row.get('SUA_NAME21', 'Unknown')}")
    except Exception as e:
        print(f"Error loading SUA shapefile: {str(e)}")
        raise
    
    # Ensure same coordinate reference system
    if sal_gdf.crs != sua_gdf.crs:
        print(f"Converting CRS...")
        sal_gdf = sal_gdf.to_crs(sua_gdf.crs)
    
    # Create mapping
    print(f"Calculating spatial relationships...")
    results = []
    total_sal = len(sal_gdf)
    start_time = time.time()
    
    # For each SAL area
    for idx, sal_row in sal_gdf.iterrows():
        if idx % 100 == 0:
            elapsed = time.time() - start_time
            progress = (idx / total_sal) * 100
            estimated_total = elapsed / (idx + 1) * total_sal if idx > 0 else 0
            remaining = estimated_total - elapsed
            print(f"Processing SAL {idx}/{total_sal} ({progress:.1f}%) - ETA: {remaining/60:.1f} minutes")
            
        # Get SAL attributes
        # Using the correct column names from your shapefile
        sal_code = str(sal_row.get('SAL_CODE21', ''))
        sal_name = str(sal_row.get('SAL_NAME21', ''))
        sal_state = str(sal_row.get('STE_NAME21', ''))  # State name column
        sal_geom = sal_row.geometry
        
        # Skip if geometry is None or invalid
        if sal_geom is None:
            print(f"Skipping SAL {sal_code} ({sal_name}) - Missing geometry")
            continue
            
        # Skip if geometry is invalid
        if not sal_geom.is_valid:
            print(f"Skipping SAL {sal_code} ({sal_name}) - Invalid geometry")
            continue
        
        # Calculate intersection with each SUA
        for _, sua_row in sua_gdf.iterrows():
            # Get SUA attributes
            # Adjust these column names if they differ in your shapefile
            sua_code = str(sua_row.get('SUA_CODE21', ''))
            sua_name = str(sua_row.get('SUA_NAME21', ''))
            sua_geom = sua_row.geometry
            
            # Skip if geometry is None
            if sua_geom is None:
                continue
                
            # Skip if geometry is invalid
            if not sua_geom.is_valid:
                continue
                
            # Check if they intersect (faster check before doing calculation)
            if sal_geom.intersects(sua_geom):
                try:
                    # Calculate overlap percentage
                    intersection = sal_geom.intersection(sua_geom)
                    overlap_pct = (intersection.area / sal_geom.area) * 100
                    
                    # Store the result
                    results.append({
                        'sal_code': sal_code,
                        'sal_name': sal_name,
                        'state': sal_state,  # Include state information
                        'sua_code': sua_code,
                        'sua_name': sua_name,
                        'overlap_pct': overlap_pct
                    })
                except Exception as e:
                    print(f"Error calculating overlap for SAL {sal_code} and SUA {sua_code}: {str(e)}")
    
    # Create DataFrame and save to CSV
    print(f"Found {len(results)} relationships between SAL and SUA areas")
    mapping_df = pd.DataFrame(results)
    mapping_df.to_csv(output_file, index=False)
    print(f"Mapping saved to: {output_file}")
    
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time/60:.2f} minutes")
    
    return str(output_file)


if __name__ == "__main__":
    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python create_sal_mapping.py <data_directory> [output_file]")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = create_sal_to_sua_mapping(data_dir, output_file)
        print(f"Successfully created mapping at: {result}")
    except Exception as e:
        print(f"Error creating mapping: {str(e)}")
        sys.exit(1)