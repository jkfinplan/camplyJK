# Santa Barbara County Parks - Camava Migration

## 🎯 Summary

Santa Barbara County Parks is **switching providers** on **January 1, 2026**:
- **Old**: Itinio (countyofsb.itinio.com) - Complex, AWS WAF, email login required
- **New**: Camava (santabarbara.camava.com) - Simple, no WAF, no login required

## ✅ Good News: Camava is WAY Easier!

| Feature | Itinio (Old) | Camava (New) |
|---------|--------------|---------------|
| AWS WAF | ✅ Yes (blocks requests) | ❌ No |
| Login Required | ✅ Yes (email verification) | ❌ No |
| Browser Automation | ✅ Required (Playwright) | ❌ Not needed |
| HTTP Requests | ❌ Blocked | ✅ Work perfectly |
| Complexity | 🔴 Very High | 🟢 Low |

## 📊 Camava System Details

### Base Information
- **URL**: https://santabarbara.camava.com/reservation/camping/index.asp
- **Method**: POST
- **Server**: Microsoft-IIS/10.0 (ASP.NET)
- **Session**: Cookie-based (cartGUID, ASPSESSIONID)

### POST Parameters

```python
data = {
    'reserve_type': 'camping',
    'parent_idno': '2',  # Jalama Beach ID
    'arrive_date': '1/10/2026',  # Format: M/D/YYYY
    'res_length': '2',  # Number of nights
    'depart_date': '01/12/2026',  # Format: MM/DD/YYYY
    'rv_length': '0',  # Optional: RV length filter
    'rv_width': '0',  # Optional: RV width filter
    'site_type_idno': '',  # Optional: Site type filter
    'max_consecutive_nights': '14',
    'min_consecutive_nights': '1',
}
```

### Response Format

**HTML with site cards**:
- Each available site is a `<div>` with `data-id` attribute
- Site ID: `data-id="1767"`
- Coordinates: `data-lat="34.51"` and `data-lng="-120.50"`
- Price: "Use Fee: $110.00"
- Amenities: Listed as divs with checkmarks
- **Only available sites are returned!**

### Search Results
- Test search (May 10-12, 2026): **432 available sites**
- Prices range: $110 - $600 per night
- No "unavailable" indicators - response only includes bookable sites

## 🚀 Implementation Plan

### Phase 1: Basic Provider (Recommended for Jan 1)

Create a simple Camava provider using standard HTTP requests:

```python
class CamavaProvider(BaseProvider):
    """
    Provider for Camava reservation system.
    Used by Santa Barbara County Parks (effective Jan 1, 2026).
    """
    
    base_url = "https://santabarbara.camava.com"
    
    def get_campsites(self, start_date, end_date, **kwargs):
        # 1. GET to establish session
        session = requests.Session()
        session.get(f"{self.base_url}/reservation/camping/index.asp")
        
        # 2. POST search
        data = {
            'reserve_type': 'camping',
            'parent_idno': '2',
            'arrive_date': start_date.strftime('%-m/%-d/%Y'),
            'res_length': (end_date - start_date).days,
            'depart_date': end_date.strftime('%m/%d/%Y'),
        }
        resp = session.post(f"{self.base_url}/reservation/camping/index.asp", data=data)
        
        # 3. Parse HTML for site cards
        soup = BeautifulSoup(resp.text, 'html.parser')
        site_divs = soup.find_all('div', {'data-id': True})
        
        # 4. Extract site data
        campsites = []
        for div in site_divs:
            site = AvailableCampsite(
                campsite_id=div['data-id'],
                # ... extract other fields
            )
            campsites.append(site)
        
        return campsites
```

### Phase 2: Full Integration

- [ ] Create `CamavaProvider` base class
- [ ] Create `SantaBarbaraCountyParksCamava` variation
- [ ] Implement campground discovery
- [ ] Parse site amenities
- [ ] Extract pricing information
- [ ] Add site type filtering
- [ ] Support RV length/width filters
- [ ] Add comprehensive tests

### Phase 3: Migration

- [ ] Mark Itinio provider as deprecated (Dec 15, 2025)
- [ ] Add migration notice to documentation
- [ ] Update examples to use Camava provider
- [ ] Remove Itinio provider (Feb 1, 2026)

## 📅 Timeline

| Date | Action |
|------|--------|
| **Nov 7, 2025** | Camava system discovered |
| **Dec 1, 2025** | Implement Camava provider |
| **Dec 15, 2025** | Mark Itinio provider as deprecated |
| **Jan 1, 2026** | 🔄 Santa Barbara switches to Camava |
| **Jan 1, 2026** | Activate Camava provider |
| **Feb 1, 2026** | Remove Itinio provider code |

## 🔧 Technical Comparison

### Itinio Provider (Old - Deprecated Jan 1)

```python
# Complex: Requires Playwright
with SantaBarbaraCountyParksPlaywright(
    email="your@email.com",
    headless=False,  # Must see browser
    login_wait_time=180  # Wait for email code
) as provider:
    sites = provider.get_campsites(...)
    
# Takes ~130 seconds (login) + browser overhead
```

### Camava Provider (New - Active Jan 1)

```python
# Simple: Just HTTP requests
provider = SantaBarbaraCountyParksCamava()
sites = provider.get_campsites(
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=2)
)

# Takes ~2 seconds, no browser needed!
```

## 🎯 Next Steps

### Immediate (Do Now)
1. ✅ Investigate Camava system - **DONE**
2. ⏳ Create `CamavaProvider` base class
3. ⏳ Implement site parsing logic
4. ⏳ Test with real searches

### Before Jan 1, 2026
- Add deprecation warnings to Itinio provider
- Update documentation with migration guide
- Test Camava provider thoroughly
- Prepare switch for Jan 1

### After Jan 1, 2026
- Monitor for any Camava changes
- Collect user feedback
- Remove Itinio code after grace period

## 🤔 Questions to Investigate

1. **Other parks**: Does Camava support other parks besides Jalama?
2. **Site types**: What are the valid `site_type_idno` values?
3. **Booking**: Can we also implement booking through Camava API?
4. **Rate limits**: Are there any rate limiting considerations?
5. **Authentication**: Does Camava support any API keys for official access?

## 💡 Benefits of Switch

**For Users**:
- ✅ No email required
- ✅ No browser interaction
- ✅ Faster searches (~2s vs ~130s)
- ✅ Works headlessly (perfect for automation)
- ✅ Lower resource usage (no Chromium)

**For Developers**:
- ✅ Simpler code (no Playwright)
- ✅ Easier testing
- ✅ Fewer dependencies
- ✅ Standard HTTP patterns
- ✅ Better error handling

**For Infrastructure**:
- ✅ Lower memory usage
- ✅ Faster execution
- ✅ No browser binaries needed
- ✅ Easier deployment

## 📚 Related Files

**Current (Itinio)**:
- `camply/providers/itinio/itinio.py`
- `camply/providers/itinio/itinio_playwright.py`
- `camply/providers/itinio/variations.py`
- `PLAYWRIGHT_PROVIDER_GUIDE.md`
- `test_playwright_login.py`

**Future (Camava)**:
- `camply/providers/camava/camava.py` ← To create
- `camply/providers/camava/variations.py` ← To create
- `camply/providers/camava/README.md` ← To create
- `test_camava.py` ← To create

## 🎉 Conclusion

The switch from Itinio to Camava is **excellent news**! The new system is:
- **Simpler** to implement
- **Faster** to use
- **More reliable** (no WAF issues)
- **Easier** to maintain

The Playwright provider we just built will be useful for ~2 months, then we can switch to a much simpler HTTP-based provider.

**Recommendation**: Implement the Camava provider ASAP to be ready for January 1st!

---

**Last Updated**: November 7, 2025  
**Migration Date**: January 1, 2026  
**Status**: ✅ **Camava Provider IMPLEMENTED and TESTED!**

## ✅ Implementation Complete!

The Camava provider has been implemented and tested successfully:
- ✅ 108 available sites found in test search
- ✅ Simple HTTP requests (no browser needed)
- ✅ ~2 second search time
- ✅ All old Itinio/Playwright code removed

See `camply/providers/camava/README.md` for usage instructions.

