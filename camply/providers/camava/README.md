# Camava Provider

Provider for Camava reservation systems used by Santa Barbara County Parks.

## Supported Parks

- **Santa Barbara County Parks**
  - Cachuma Lake (campground_id=1)
  - Jalama Beach (campground_id=2)

## Usage

### Command Line

```bash
# Search Jalama Beach
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-05-01 \
  --end-date 2026-05-03

# Search Cachuma Lake
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 1 \
  --start-date 2026-05-01 \
  --end-date 2026-05-03
```

### Python API

```python
from datetime import datetime, timedelta
from camply.providers.camava import SantaBarbaraCountyParks

provider = SantaBarbaraCountyParks()

start_date = datetime.now() + timedelta(days=14)
end_date = start_date + timedelta(days=2)

# Search Jalama Beach
campsites = provider.get_campsites(
    campground_id=2,
    start_date=start_date,
    end_date=end_date
)

# List available campgrounds
campgrounds = provider.find_campgrounds()
for cg in campgrounds:
    print(f"{cg.facility_name} (ID: {cg.facility_id})")
```

## Notes

- System available starting January 1, 2026
- No login required for searching
- Returns only available sites
