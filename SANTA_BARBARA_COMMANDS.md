# Santa Barbara County Parks - Camply Commands

Quick reference guide for searching Santa Barbara County Parks using camply.

## 🏕️ Jalama Beach

### Basic Campsite Search
```bash
# Search for any available campsite at Jalama Beach
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-05-10 \
  --end-date 2026-05-12
```

### Weekend Search
```bash
# Only show weekend availability (Friday/Saturday nights)
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-05-01 \
  --end-date 2026-05-31 \
  --weekends
```

### Continuous Monitoring
```bash
# Continuously check for availability and get notified
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-07-04 \
  --end-date 2026-07-07 \
  --continuous \
  --notifications pushover
```

### Specific Number of Nights
```bash
# Search for exactly 3 consecutive nights
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-06-01 \
  --end-date 2026-06-30 \
  --nights 3
```

### RV Sites Only
```bash
# Filter for RV-compatible sites with minimum length
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-05-15 \
  --end-date 2026-05-17 \
  --equipment RV 40
```

## 🏊 Cachuma Lake

### Basic Campsite Search
```bash
# Search Cachuma Lake campsites
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 1 \
  --start-date 2026-05-10 \
  --end-date 2026-05-12
```

### Cabins at Cachuma Lake
```bash
# Note: If Cachuma has cabins, they may be under a different campground ID
# Check available facility types first with:
camply campgrounds --provider SantaBarbaraCountyParks
```

## 🔍 General Search Commands

### Find All Santa Barbara Campgrounds
```bash
# List all available campgrounds
camply campgrounds --provider SantaBarbaraCountyParks
```

### Test Your Notification Setup
```bash
# Make sure notifications work before setting up monitoring
camply test-notifications pushover
```

### List Available Providers
```bash
# See all camply providers
camply providers
```

## 📅 Common Date Patterns

### Memorial Day Weekend 2026
```bash
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-05-22 \
  --end-date 2026-05-25 \
  --continuous \
  --notifications silent
```

### 4th of July Week 2026
```bash
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-07-03 \
  --end-date 2026-07-06 \
  --continuous \
  --notifications email
```

### Labor Day Weekend 2026
```bash
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-09-04 \
  --end-date 2026-09-07 \
  --continuous
```

## 🔔 Notification Types

Available notification options:
- `silent` - Just log to console (default)
- `pushover` - Pushover app notifications
- `email` - Email notifications
- `telegram` - Telegram bot
- `slack` - Slack webhook
- `ntfy` - ntfy.sh service
- `pushbullet` - Pushbullet
- `twilio` - SMS via Twilio
- `webhook` - Custom webhook
- `apprise` - Apprise library (supports many services)

Example with multiple notification types:
```bash
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-06-01 \
  --end-date 2026-06-15 \
  --continuous \
  --notifications pushover \
  --notifications email
```

## 📝 Using YAML Configuration

Create a file `jalama-search.yaml`:
```yaml
provider: SantaBarbaraCountyParks
campgrounds:
  - 2  # Jalama Beach
start_date: 2026-05-01
end_date: 2026-05-31
continuous: true
notifications:
  - pushover
polling_interval: 10
```

Then run:
```bash
camply campsites --yaml-config jalama-search.yaml
```

## 🎯 Pro Tips

### 1. Save Searches Offline
Useful for running camply as a cron job:
```bash
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-05-01 \
  --end-date 2026-05-31 \
  --search-once \
  --offline-search \
  --notifications pushover
```

### 2. Search Forever Mode
Keep searching even after finding availability:
```bash
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-06-01 \
  --end-date 2026-08-31 \
  --search-forever \
  --notifications email
```

### 3. Faster Polling for Hot Dates
Check every 5 minutes (minimum):
```bash
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-07-04 \
  --end-date 2026-07-06 \
  --continuous \
  --polling-interval 5 \
  --notifications pushover
```

### 4. Specific Day of Week
Search only for Friday arrivals:
```bash
camply campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-05-01 \
  --end-date 2026-05-31 \
  --day Friday
```

## 🆔 Campground IDs

| Park | Campground ID | Notes |
|------|---------------|-------|
| Jalama Beach | 2 | Beach camping, RV and tent sites |
| Cachuma Lake | 1 | Lake camping, may have cabins |

To find more campground IDs:
```bash
camply campgrounds --provider SantaBarbaraCountyParks
```

## 🐛 Debugging

Enable debug mode to see detailed logs:
```bash
camply --debug campsites \
  --provider SantaBarbaraCountyParks \
  --campground 2 \
  --start-date 2026-05-10 \
  --end-date 2026-05-12
```

## 📖 More Information

- Provider Documentation: `camply/providers/camava/README.md`
- General camply docs: https://juftin.com/camply
- Test script: `python test_camava.py`

---

**Note**: These commands will work starting **January 1, 2026** when Santa Barbara County Parks switches to the Camava system.

**Quick Test**: Try a search for May 2026 - the system is already live!

