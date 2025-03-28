import csv
import random
import ipaddress
from datetime import datetime, timedelta

inputcsv = 'useractivityvariation4.csv'
outputcsv = 'useractivityvariation5.csv'

devicetypes = ['Windows', 'Mac', 'Linux', 'iOS', 'Android']

TIMEZONE_MAPPING = {
    "Asia": {
        "Asia/Kolkata": (8.0, 37.0, 68.0, 97.0),
        "Asia/Dubai": (22.0, 26.0, 51.0, 56.0),
        "Asia/Shanghai": (20.0, 54.0, 100.0, 124.0),
        "Asia/Tokyo": (24.0, 46.0, 122.0, 146.0),
        "Asia/Bangkok": (5.0, 21.0, 97.0, 108.0),
    },
    "Europe": {
        "Europe/London": (49.0, 59.0, -10.0, 2.0),
        "Europe/Berlin": (47.0, 55.0, 6.0, 15.0),
        "Europe/Paris": (42.0, 51.0, -5.0, 8.0),
        "Europe/Moscow": (54.0, 70.0, 30.0, 50.0),
        "Europe/Madrid": (36.0, 44.0, -9.0, 4.0),
    },
    "Africa": {
        "Africa/Cairo": (22.0, 32.0, 25.0, 36.0),
        "Africa/Lagos": (4.0, 14.0, 3.0, 15.0),
        "Africa/Johannesburg": (-35.0, -22.0, 16.0, 32.0),
        "Africa/Nairobi": (-5.0, 5.0, 34.0, 42.0),
        "Africa/Casablanca": (27.0, 36.0, -14.0, -1.0),
    },
    "America": {
        "America/New_York": (35.0, 45.0, -80.0, -70.0),
        "America/Chicago": (30.0, 40.0, -100.0, -85.0),
        "America/Denver": (35.0, 45.0, -110.0, -100.0),
        "America/Los_Angeles": (30.0, 42.0, -125.0, -115.0),
        "America/Sao_Paulo": (-30.0, -20.0, -55.0, -40.0),
    }
}

def get_new_continent(excluded_continent):
    available_continents = list(TIMEZONE_MAPPING.keys())

    if excluded_continent in available_continents:
        available_continents.remove(excluded_continent)

    return random.choice(available_continents)

def get_new_timezone(continent):
    return random.choice(list(TIMEZONE_MAPPING[continent].keys()))

def generate_entry(latest_entry):
    modified_entry = latest_entry.copy()

    old_lat, old_lon = float(latest_entry['Latitude']), float(latest_entry['Longitude'])
    old_continent = None

    for continent, zones in TIMEZONE_MAPPING.items():
        for _, (lat_min, lat_max, lon_min, lon_max) in zones.items():
            if lat_min <= old_lat <= lat_max and lon_min <= old_lon <= lon_max:
                old_continent = continent
                break
        if old_continent:
            break

    new_continent = get_new_continent(old_continent)
    new_timezone = get_new_timezone(new_continent)
    lat_min, lat_max, lon_min, lon_max = TIMEZONE_MAPPING[new_continent][new_timezone]

    modified_entry['Latitude'] = round(random.uniform(lat_min, lat_max), 6)
    modified_entry['Longitude'] = round(random.uniform(lon_min, lon_max), 6)
    modified_entry['Timezone'] = new_timezone

    modified_entry["IPaddress"] = str(ipaddress.IPv4Address(random.randint(0, 2**32-1)))
    modified_entry["DeviceInfo"] = random.choice(devicetypes)

    original_time = datetime.strptime(latest_entry['LoginTime'], '%Y-%m-%d %H:%M:%S')
    time_variation = timedelta(days=random.randint(-1, 1), hours=random.randint(-6, 6))
    modified_entry["LoginTime"] = (original_time + time_variation).strftime('%Y-%m-%d %H:%M:%S')

    # **Randomized Typing Speed & Mouse Speed**
    modified_entry["TypingSpeed"] = random.randint(10, 200)
    modified_entry["MouseSpeed"] = random.randint(200, 2000)

    return modified_entry

# Read the original CSV and store all entries
user_entries = {}

with open(inputcsv, mode='r', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        user_id = row['userID']
        if user_id not in user_entries:
            user_entries[user_id] = []
        user_entries[user_id].append(row)

# Keep only the latest 6 entries per user
filtered_entries = []
for user_id, entries in user_entries.items():
    entries = sorted(entries, key=lambda x: datetime.strptime(x['LoginTime'], '%Y-%m-%d %H:%M:%S'))  # Sort by LoginTime
    latest_entries = entries[-6:]  # Keep only last 6
    filtered_entries.extend(latest_entries)

# Generate one new modified entry per user
new_entries = [generate_entry(entries[-1]) for user_id, entries in user_entries.items()]

# Write new CSV file
with open(outputcsv, mode='w', newline='', encoding='utf-8') as outfile:
    fieldnames = list(filtered_entries[0].keys())  # Get headers from existing data
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(filtered_entries)  # Write last 6 entries per user
    writer.writerows(new_entries)  # Append one new generated entry per user

print('✅ New CSV file created with the last 6 entries per user + one new modified entry per user.')
