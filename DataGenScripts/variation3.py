import csv
import random
import ipaddress
from datetime import datetime, timedelta
from collections import defaultdict

inputcsv = 'useractivityvariation2.csv'
outputcsv = 'useractivityvariation3.csv'

devicetypes = ['Windows', 'Mac', 'Linux', 'iOS', 'Android']

TIMEZONE_MAPPING = {
    "Asia": {"Asia/Kolkata": (8.0, 37.0, 68.0, 97.0)},
    "Europe": {"Europe/London": (49.0, 59.0, -10.0, 2.0)},
    "America": {"America/New_York": (35.0, 45.0, -80.0, -70.0)}
}

def getcontinent(lat, lon):
    for continent, timezones in TIMEZONE_MAPPING.items():
        for tz, (lat_min, lat_max, lon_min, lon_max) in timezones.items():
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return continent
    return "Asia"

def gettimezone(continent, lat, lon):
    if continent not in TIMEZONE_MAPPING:
        return "Asia/Kolkata"
    return random.choice(list(TIMEZONE_MAPPING[continent].keys()))

def newipaddress():
    return str(ipaddress.IPv4Address(random.randint(0, 2**32-1)))

def generate_variation(row):
    """Creates a new variation based on the given row"""
    rowcopy = row.copy()
    continent = getcontinent(float(row['Latitude']), float(row['Longitude']))

    rowcopy["IPaddress"] = newipaddress()
    rowcopy["DeviceInfo"] = random.choice(devicetypes)

    latshift = random.uniform(-6, 6)
    longshift = random.uniform(-10, 10)

    rowcopy["Latitude"] = float(row['Latitude']) + round(latshift, 6)
    rowcopy["Longitude"] = float(row['Longitude']) + round(longshift, 6)
    rowcopy["Timezone"] = gettimezone(continent, rowcopy["Latitude"], rowcopy["Longitude"])

    originaltime = datetime.strptime(row['LoginTime'], '%Y-%m-%d %H:%M:%S')
    timevariation = timedelta(days=random.randint(2, 4), hours=random.randint(-6, 6))
    rowcopy["LoginTime"] = (originaltime + timevariation).strftime('%Y-%m-%d %H:%M:%S')

    rowcopy["TypingSpeed"] = max(10, min(200, int(row['TypingSpeed']) + random.randint(-15, 15)))
    rowcopy["MouseSpeed"] = max(200, min(2000, float(row['MouseSpeed']) + random.randint(-150, 150)))

    return rowcopy

# Dictionary to store rows for each user
users_data = defaultdict(list)

with open(inputcsv, mode='r', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        user_id = row['userID']  # Change to appropriate column name if needed
        users_data[user_id].append(row)

with open(outputcsv, mode='w', newline='', encoding='utf-8') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()

    for user_id, rows in users_data.items():
        # Keep the first 4 rows for each user unchanged
        for i in range(min(4, len(rows))):
            writer.writerow(rows[i])

        # Generate one new row from the 4th row (if available)
        if len(rows) >= 4:
            new_row = generate_variation(rows[3])
            writer.writerow(new_row)

print('CSV file created with 1 new variation per user.')
