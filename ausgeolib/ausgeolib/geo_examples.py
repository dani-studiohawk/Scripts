"""
Example usage of geo_utilities for Australian geographic analysis
"""

import os
import pandas as pd
from ausgeolib import GeoHelper
from geo_utilities import (
    export_to_csv,
    get_population_by_state,
    compare_cities,
    find_suburbs_by_name,
    get_suburb_demographics,
    export_city_data,
    get_geographic_coverage,
    compare_major_cities,
    find_all_beaches
)

# Create output directory for examples
output_dir = "geo_analysis_results"
os.makedirs(output_dir, exist_ok=True)

def example_1_state_populations():
    """Example: Get population by state and export to CSV"""
    print("\n=== Example 1: State Populations ===")
    
    # Get state populations
    state_pops = get_population_by_state()
    print("Population by state:")
    print(state_pops)
    
    # Export to CSV
    export_to_csv(state_pops, "state_populations.csv", output_dir)


def example_2_compare_cities():
    """Example: Compare major cities"""
    print("\n=== Example 2: City Comparison ===")
    
    # List of cities to compare
    cities = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"]
    
    # Compare by population
    pop_comparison = compare_cities(cities, "population")
    print("\nComparison by population:")
    print(pop_comparison[["city", "population", "suburb_count"]])
    
    # Export to CSV
    export_to_csv(pop_comparison, "city_comparison.csv", output_dir)
    


def example_3_find_suburbs():
    """Example: Find suburbs with specific patterns"""
    print("\n=== Example 3: Finding Suburbs ===")
    
    # Find all suburbs with "Park" in the name
    park_suburbs = find_suburbs_by_name("Park")
    print(f"\nFound {len(park_suburbs)} suburbs with 'Park' in the name")
    print(park_suburbs[["sal_name", "state"]].head())
    
    # Find beaches in Queensland
    qld_beaches = find_suburbs_by_name("Beach", state="Queensland")
    print(f"\nFound {len(qld_beaches)} beaches in Queensland")
    print(qld_beaches[["sal_name", "state"]].head())
    
    # Export results
    export_to_csv(park_suburbs, "park_suburbs.csv", output_dir)
    export_to_csv(qld_beaches, "qld_beaches.csv", output_dir)


def example_4_suburb_demographics():
    """Example: Get detailed demographics for a suburb"""
    print("\n=== Example 4: Suburb Demographics ===")
    
    # Get demographics for Bondi Beach (you'll need to replace with a valid SAL code)
    # First find the SAL code
    bondi = find_suburbs_by_name("Bondi Beach")
    if len(bondi) > 0:
        sal_code = bondi.iloc[0]['sal_code']
        demographics = get_suburb_demographics(sal_code)
        
        print(f"\nDemographics for {demographics.get('name', 'Unknown')}:")
        
        if 'demographics' in demographics and 'total' in demographics['demographics']:
            total_stats = demographics['demographics']['total']
            print(f"Total population: {total_stats['total']}")
            print(f"Males: {total_stats['male']}")
            print(f"Females: {total_stats['female']}")
            
            if '25_34' in demographics['demographics']:
                print(f"Population aged 25-34: {demographics['demographics']['25_34']['total']}")
    else:
        print("Bondi Beach not found in the data")


def example_5_export_city_data():
    """Example: Export comprehensive data for a city"""
    print("\n=== Example 5: Export City Data ===")
    
    # Export data for Brisbane
    exported = export_city_data("Brisbane", output_dir)
    
    print(f"\nExported {len(exported)} files for Brisbane:")
    for key, path in exported.items():
        print(f"- {key}: {path}")


def example_6_geographic_coverage():
    """Example: Calculate urban coverage by state"""
    print("\n=== Example 6: Geographic Coverage ===")
    
    # Get coverage statistics
    coverage = get_geographic_coverage()
    print("\nUrban coverage by state:")
    if 'urban_pop_percentage' in coverage.columns:
        print(coverage[["state", "urban_percentage", "urban_pop_percentage"]])
    else:
        print(coverage[["state", "urban_percentage"]])
    
    # Export to CSV
    export_to_csv(coverage, "urban_coverage.csv", output_dir)


def run_all_examples():
    """Run all examples"""
    print("Running all geo_utilities examples...")
    print(f"Results will be saved to: {os.path.abspath(output_dir)}")
    
    example_1_state_populations()
    example_2_compare_cities()
    example_3_find_suburbs()
    example_4_suburb_demographics()
    example_5_export_city_data()
    example_6_geographic_coverage()
    
    print("\nAll examples completed!")


if __name__ == "__main__":
    run_all_examples()