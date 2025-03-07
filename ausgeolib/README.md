# Australian Geographic Database

A simple interface for querying Australian geographic boundaries and population data.

## Installation

```bash
pip install -e .

Usage

from ausgeolib import GeoDatabase

# Initialize the database
db = GeoDatabase()

# Get population of Sydney
sydney_pop = db.get_population("Sydney", "sua")

# Get all LGAs in Sydney
sydney_lgas = db.get_areas_in_sua("Sydney", "lga")

# Find which SUA contains Blacktown
blacktown_sua = db.get_sua_for_area("Blacktown", "lga")

### For `ausgeolib/__init__.py`:
Open this file and add:
```python
from .database import GeoDatabase

__all__ = ['GeoDatabase']