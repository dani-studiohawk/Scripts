# AUSGEOLIB: Australian Geographic Analysis Library

## Overview

AUSGEOLIB is a Python library for analyzing Australian geographic data, focusing on the relationships between different geographic boundaries (LGA, SA2, SAL, SUA) and population data integration. The library provides an intuitive interface for querying geographic data, analyzing population statistics, and working with spatial relationships.

## Core Components

The library consists of three main components:

1. **GeoDatabase**: Low-level data access class that handles loading and parsing geographic data files
2. **GeoHelper**: High-level interface that provides natural language-like functions for common geographic queries
3. **Geo Utilities**: Additional utility functions for data export and specialized analyses

## Table of Contents

- [Installation](#installation)
- [Required Data](#required-data)
- [GeoDatabase Class](#geodatabase-class)
- [GeoHelper Class](#geohelper-class)
- [Geo Utilities](#geo-utilities)
- [Examples](#examples)
- [Extending the Library](#extending-the-library)

## Installation

```bash
# From the package directory
pip install -e .
```

## Required Data

The library expects a specific directory structure for geographic data files:

```
Geolocation Files/
├── Population/
│   ├── lga_population.csv
│   ├── sua_population.csv
│   └── sal_population.csv
├── Relationships/
│   ├── lga_to_sua.csv
│   ├── sa2_to_sua.csv
│   └── sal_to_sua.csv
└── Boundaries/
    ├── LGA_2024_AUST_GDA2020/
    │   └── LGA_2024_AUST_GDA2020.shp (and related files)
    ├── SUA_2021_AUST_GDA2020/
    │   └── SUA_2021_AUST_GDA2020.shp (and related files)
    └── SAL_2021_AUST_GDA2020_SHP/
        └── SAL_2021_AUST_GDA2020.shp (and related files)
```

## GeoDatabase Class

The `GeoDatabase` class provides access to Australian geographic data files and offers methods to query relationships between different geographic boundaries.

### Initialization

```python
from ausgeolib import GeoDatabase

# Initialize with default data directory
db = GeoDatabase()

# Or specify a custom data directory
db = GeoDatabase("path/to/data/directory")
```

### Methods

#### `get_population(area_name, geo_type)`

Get population for a specific area.

**Parameters:**
- `area_name` (str): Name or code of the area
- `geo_type` (str): Geography type ('sua', 'lga', 'sa2', or 'sal')

**Returns:**
- (int or None): Population value or None if not found

**Example:**
```python
# Get population of Sydney SUA
sydney_pop = db.get_population("Sydney", "sua")

# Get population of Blacktown LGA
blacktown_pop = db.get_population("Blacktown", "lga")

# Get population of a specific SAL area
sal_pop = db.get_population("10001", "sal")
```

#### `get_population_by_demographics(area_name, geo_type, age_group=None, gender=None)`

Get population breakdown by demographics.

**Parameters:**
- `area_name` (str): Name or code of the area
- `geo_type` (str): Geography type ('sal', 'lga', 'sua', etc.)
- `age_group` (str, optional): Age group to filter by (e.g., '0_4', '25_34', 'total')
- `gender` (str, optional): Gender to filter by ('M', 'F', or None for total)

**Returns:**
- (int or dict): Population value or dictionary of demographic breakdowns

**Example:**
```python
# Get full demographic breakdown
demographics = db.get_population_by_demographics("10001", "sal")

# Get specific demographic
young_males = db.get_population_by_demographics("10001", "sal", age_group="0_4", gender="M")

# Get all age groups for females
female_ages = db.get_population_by_demographics("10001", "sal", gender="F")
```

#### `get_areas_in_sua(sua_name, geo_type, min_overlap=50)`

Get all areas of a specific type within a SUA.

**Parameters:**
- `sua_name` (str): Name of the Significant Urban Area
- `geo_type` (str): Geography type to retrieve ('lga', 'sa2', or 'sal')
- `min_overlap` (float, default=50): Minimum overlap percentage to include

**Returns:**
- (DataFrame): DataFrame with areas in the SUA

**Example:**
```python
# Get all suburbs in Sydney
sydney_suburbs = db.get_areas_in_sua("Sydney", "sal")

# Get all LGAs in Melbourne with at least 75% overlap
melbourne_lgas = db.get_areas_in_sua("Melbourne", "lga", min_overlap=75)
```

#### `get_sua_for_area(area_name, geo_type, min_overlap=50)`

Find which SUA an area belongs to.

**Parameters:**
- `area_name` (str): Name of the area
- `geo_type` (str): Geography type ('lga', 'sa2', or 'sal')
- `min_overlap` (float, default=50): Minimum overlap percentage to include

**Returns:**
- (DataFrame): DataFrame with SUAs that contain this area

**Example:**
```python
# Find which SUA Blacktown LGA belongs to
blacktown_sua = db.get_sua_for_area("Blacktown", "lga")

# Find which SUA a SAL area belongs to
sal_sua = db.get_sua_for_area("10001", "sal")
```

## GeoHelper Class

The `GeoHelper` class provides higher-level, more intuitive functions for geographic analysis.

### Initialization

```python
from ausgeolib import GeoHelper

# Initialize with default data directory
helper = GeoHelper()

# Or specify a custom data directory
helper = GeoHelper("path/to/data/directory")
```

### Methods

#### `get_suburbs_in_metropolitan_area(city_name, min_overlap=50)`

Get all suburbs (SAL areas) within a metropolitan area.

**Parameters:**
- `city_name` (str): Name of the metropolitan area (SUA)
- `min_overlap` (float, default=50): Minimum percentage overlap required

**Returns:**
- (DataFrame): DataFrame with suburb information sorted by population

**Example:**
```python
# Get all suburbs in Sydney
sydney_suburbs = helper.get_suburbs_in_metropolitan_area("Sydney")
```

#### `get_suburbs_by_distance(city_name, max_distance_km=20, sort_by='population')`

Get suburbs within a certain distance from a metropolitan area's center.

**Parameters:**
- `city_name` (str): Name of the metropolitan area (SUA)
- `max_distance_km` (float, default=20): Approximate maximum distance in kilometers
- `sort_by` (str, default='population'): Sort criterion ('population', 'distance', 'overlap', 'name')

**Returns:**
- (DataFrame): DataFrame with suburbs sorted by the specified criterion

**Example:**
```python
# Get suburbs within 15km of Melbourne
melbourne_nearby = helper.get_suburbs_by_distance("Melbourne", 15)

# Get suburbs within 10km of Brisbane, sorted by distance
brisbane_nearby = helper.get_suburbs_by_distance("Brisbane", 10, sort_by='distance')
```

#### `get_largest_suburbs(n=10, state=None)`

Get the largest suburbs by population.

**Parameters:**
- `n` (int, default=10): Number of suburbs to return
- `state` (str, optional): Filter by state ('New South Wales', 'Victoria', etc.)

**Returns:**
- (DataFrame): DataFrame with the largest suburbs

**Example:**
```python
# Get the 10 largest suburbs in Australia
largest = helper.get_largest_suburbs(10)

# Get the 5 largest suburbs in Queensland
qld_largest = helper.get_largest_suburbs(5, state="Queensland")
```

#### `get_major_metropolitan_areas(min_population=100000)`

Get a list of major metropolitan areas (SUAs) by population.

**Parameters:**
- `min_population` (int, default=100000): Minimum population to be considered major

**Returns:**
- (DataFrame): DataFrame with metropolitan areas and their populations

**Example:**
```python
# Get all major cities
major_cities = helper.get_major_metropolitan_areas()

# Get very large cities (1M+)
large_cities = helper.get_major_metropolitan_areas(1000000)
```

#### `get_all_suburbs_in_state(state, min_population=None)`

Get all suburbs in a specific state.

**Parameters:**
- `state` (str): State name ('New South Wales', 'Victoria', etc.)
- `min_population` (int, optional): Minimum population to include

**Returns:**
- (DataFrame): DataFrame with all suburbs in the state

**Example:**
```python
# Get all suburbs in Victoria
vic_suburbs = helper.get_all_suburbs_in_state("Victoria")

# Get all suburbs in NSW with at least 5000 people
nsw_large_suburbs = helper.get_all_suburbs_in_state("New South Wales", min_population=5000)
```

## Geo Utilities

Additional utility functions for data export and specialized analyses.

### Data Export

#### `export_to_csv(data, filename, output_dir=None)`

Export DataFrame to CSV file.

**Parameters:**
- `data` (DataFrame): DataFrame to export
- `filename` (str): Name of the output file (without path)
- `output_dir` (str, optional): Directory to save the file (defaults to current directory)

**Returns:**
- (str): Path to the saved file

**Example:**
```python
from geo_utilities import export_to_csv

# Export data to CSV
export_to_csv(sydney_suburbs, "sydney_suburbs.csv", "output_directory")
```

#### `export_city_data(city_name, output_dir=None)`

Export comprehensive data for a city to CSV files.

**Parameters:**
- `city_name` (str): Name of the city to export data for
- `output_dir` (str, optional): Directory to save the files

**Returns:**
- (dict): Dictionary with paths to exported files

**Example:**
```python
from geo_utilities import export_city_data

# Export comprehensive data for Sydney
exported_files = export_city_data("Sydney", "output_directory")
```

### Data Analysis

#### `get_population_by_state()`

Get population breakdown by state.

**Returns:**
- (DataFrame): DataFrame with state populations

**Example:**
```python
from geo_utilities import get_population_by_state

# Get population by state
state_populations = get_population_by_state()
```

#### `compare_cities(cities, metric='population')`

Compare multiple cities on a given metric.

**Parameters:**
- `cities` (list): List of city names to compare
- `metric` (str, default='population'): Metric to compare ('population', 'area', 'suburb_count')

**Returns:**
- (DataFrame): DataFrame with comparison results

**Example:**
```python
from geo_utilities import compare_cities

# Compare major cities
cities = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"]
comparison = compare_cities(cities, "population")
```

#### `find_suburbs_by_name(name_pattern, state=None)`

Find suburbs whose names match a pattern.

**Parameters:**
- `name_pattern` (str): Pattern to match in suburb names
- `state` (str, optional): Filter by state

**Returns:**
- (DataFrame): DataFrame with matching suburbs

**Example:**
```python
from geo_utilities import find_suburbs_by_name

# Find all beach suburbs
beaches = find_suburbs_by_name("Beach")

# Find all park suburbs in Victoria
vic_parks = find_suburbs_by_name("Park", state="Victoria")
```

#### `get_suburb_demographics(suburb_code)`

Get detailed demographic breakdown for a suburb.

**Parameters:**
- `suburb_code` (str): SAL code for the suburb

**Returns:**
- (dict): Dictionary with demographic information

**Example:**
```python
from geo_utilities import get_suburb_demographics

# Get demographics for a suburb
demographics = get_suburb_demographics("10001")
```

#### `get_geographic_coverage()`

Calculate how much of each state is covered by SUAs.

**Returns:**
- (DataFrame): DataFrame with coverage statistics by state

**Example:**
```python
from geo_utilities import get_geographic_coverage

# Get urban coverage statistics
coverage = get_geographic_coverage()
```

### Convenience Functions

The library also includes several convenience functions for common tasks:

```python
from geo_utilities import (
    export_sydney_data,       # Export all Sydney data
    export_melbourne_data,    # Export all Melbourne data
    compare_major_cities,     # Compare Australia's major cities
    find_all_beaches          # Find all beach suburbs
)
```

## Examples

### Basic Usage

```python
from ausgeolib import GeoDatabase, GeoHelper

# Initialize database and helper
db = GeoDatabase()
helper = GeoHelper()

# Get population of Sydney
sydney_pop = db.get_population("Sydney", "sua")
print(f"Sydney population: {sydney_pop}")

# Get all suburbs in Melbourne
melbourne_suburbs = helper.get_suburbs_in_metropolitan_area("Melbourne")
print(f"Melbourne has {len(melbourne_suburbs)} suburbs")

# Get suburbs near Brisbane
brisbane_nearby = helper.get_suburbs_by_distance("Brisbane", 15)
print(f"Found {len(brisbane_nearby)} suburbs within 15km of Brisbane")
```

### Using Utilities

```python
from geo_utilities import (
    export_to_csv,
    compare_cities,
    find_suburbs_by_name
)

# Compare major cities
cities = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"]
comparison = compare_cities(cities, "population")
print(comparison)

# Export to CSV
export_to_csv(comparison, "city_comparison.csv", "output")

# Find all beach suburbs
beaches = find_suburbs_by_name("Beach")
print(f"Found {len(beaches)} beach suburbs in Australia")
```

## Extending the Library

### Adding New Geography Types

To add support for a new geography type (e.g., SA3 areas):

1. Add mapping files (e.g., sa3_to_sua.csv) to the Relationships directory
2. Add population data (e.g., sa3_population.csv) to the Population directory
3. Update the GeoDatabase class to handle the new geography type

### Creating Custom Utility Functions

You can add custom utility functions to the geo_utilities.py file:

```python
def my_custom_analysis(param1, param2):
    """
    Perform custom analysis on geographic data
    
    Parameters:
    -----------
    param1 : type
        Description
    param2 : type
        Description
        
    Returns:
    --------
    type
        Description
    """
    helper = GeoHelper()
    # Implement your analysis...
    return results
```

## License

This library is for internal use and is not licensed for public distribution.

## Acknowledgements

This library uses data from the Australian Bureau of Statistics and other public sources.