# Camava Provider

Provider for Camava reservation systems used by Santa Barbara County Parks and potentially other parks.

## Supported Parks

- **Santa Barbara County Parks** - Jalama Beach (starting January 1, 2026)

## Features

✅ **Simple HTTP requests** - No browser automation needed  
✅ **No login required** - Anonymous access  
✅ **No AWS WAF** - Works without special handling  
✅ **Fast** - Searches complete in ~2 seconds  
✅ **Returns only available sites** - Easy parsing  

## Usage

### Basic Search

```python
from datetime import datetime, timedelta
from camply.providers.camava import SantaBarbaraCountyParks

# Initialize provider
provider = SantaBarbaraCountyParks()

# Search for campsites
start_date = datetime.now() + timedelta(days=14)
end_date = start_date + timedelta(days=2)

campsites = provider.get_campsites(
    campground_id=2,
    start_date=start_date,
    end_date=end_date
)

print(f"Found {len(campsites)} available sites!")
for site in campsites:
    print(f"- {site.campsite_site_name}: {site.campsite_type}")
```

### Find Campgrounds

```python
# Get campground information
campgrounds = provider.find_campgrounds()

for cg in campgrounds:
    print(f"{cg.facility_name} (ID: {cg.facility_id})")
```

## Technical Details

### System Information

- **Backend**: Microsoft IIS / ASP.NET
- **Session**: Cookie-based (cartGUID, ASPSESSIONID)
- **Method**: POST to `/reservation/camping/index.asp`
- **Response**: HTML with site cards (data-id attributes)

### POST Parameters

```python
{
    'reserve_type': 'camping',
    'parent_idno': '2',  # Park ID
    'arrive_date': '5/10/2026',  # M/D/YYYY format
    'res_length': '2',  # Number of nights
    'depart_date': '05/12/2026',  # MM/DD/YYYY format
    'rv_length': '0',  # Optional filter
    'rv_width': '0',  # Optional filter
    'site_type_idno': '',  # Optional site type
}
```

### Response Format

HTML with site divs:

```html
<div data-id="1767" data-lat="34.51" data-lng="-120.50" class="panto-coordinates">
    Site 47
    Use Fee: $110.00
    Persons: 8
    <!-- Additional site details -->
</div>
```

Each available site includes:
- Site ID (`data-id`)
- Coordinates (lat/lng)
- Site name/number
- Price
- Occupancy
- Amenities

## Comparison to Previous System (Itinio)

| Feature | Camava (New) | Itinio (Old) |
|---------|--------------|--------------|
| AWS WAF | ❌ No | ✅ Yes (blocked requests) |
| Login | ❌ No | ✅ Yes (email verification) |
| Browser | ❌ Not needed | ✅ Required (Playwright) |
| Speed | 🟢 ~2 seconds | 🔴 ~130 seconds |
| Complexity | 🟢 Simple | 🔴 Very complex |
| Dependencies | 🟢 requests + bs4 | 🔴 Playwright + browser |

## Performance

**Typical search**: ~2 seconds
- Initial GET: ~500ms
- POST search: ~1000ms  
- HTML parsing: ~500ms

**No rate limiting observed** (but use responsibly!)

## Limitations

- Currently only supports Jalama Beach
- HTML parsing dependent on page structure
- No booking functionality (search only)

## Future Enhancements

- [ ] Support for additional Camava parks
- [ ] Site type filtering
- [ ] RV length/width filters
- [ ] Booking integration (if possible)
- [ ] Better deduplication of sites

## Migration from Itinio

If you were using the old Itinio/Playwright provider:

**Old way** (complex):
```python
# Required browser automation
with SantaBarbaraCountyParksPlaywright(
    email="your@email.com",
    headless=False,
    login_wait_time=180
) as provider:
    sites = provider.get_campsites(...)
```

**New way** (simple):
```python
# Just works!
provider = SantaBarbaraCountyParks()
sites = provider.get_campsites(
    campground_id=2,
    start_date=start,
    end_date=end
)
```

## Support

**Issues**: Create a GitHub issue with "Camava" label  
**Santa Barbara County Parks**: https://santabarbara.camava.com  
**System goes live**: January 1, 2026

## Example Output

```
INFO: 🏕️  Searching Jalama Beach County Park
INFO:    Dates: 2026-05-10 to 2026-05-12
INFO:    ✓ Found 108 available campsite(s)

1. Site 47 - Tent - up to 8 people
2. Site 45 - Tent - up to 8 people  
3. Site 44 - Tent - up to 8 people
...
```

## Contributing

To add support for additional Camava parks:

1. Find the park's `parent_idno` value
2. Create a new class in `variations.py`
3. Set `base_url`, `parent_id`, and `park_name`
4. Test and submit PR!

---

**Last Updated**: November 7, 2025  
**Status**: ✅ Tested and Working  
**Available**: January 1, 2026

