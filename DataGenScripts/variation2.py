import csv
import random
import ipaddress
from datetime import datetime, timedelta

inputcsv = 'useractivityvariation.csv'
outputcsv = 'useractivityvariation2.csv'

devicetypes = ['Windows', 'Mac', 'Linux', 'iOS', 'Android']

def generaterandomip():
    return ipaddress.IPv4Address(random.randint(0, 2**32-1))

def majorvariation(row):
    rowcopy = row.copy()

    rowcopy['IPaddress'] = generaterandomip()

    rowcopy['DeviceInfo'] = random.choice(devicetypes)

    rowcopy['Latitude'] = float(row['Latitude']) + round(random.uniform(-6, 6), 6)
    rowcopy['Longitude'] = float(row['Longitude']) + round(random.uniform(-6, 6), 6)

    originaltime = datetime.strptime(row['LoginTime'], '%Y-%m-%d %H:%M:%S')
    timevariation = timedelta(days=2, hours=random.randint(-8, 8))
    rowcopy['LoginTime'] = (originaltime + timevariation).strftime('%Y-%m-%d %H:%M:%S')

    newTypingSpeed = int(row['TypingSpeed']) + random.randint(-12, 12)
    rowcopy['TypingSpeed'] = max(10, min(200, newTypingSpeed))

    newMouseSpeed = float(row['MouseSpeed']) + random.randint(-120, 120)
    rowcopy['MouseSpeed'] = max(200, min(2000, newMouseSpeed))

    return rowcopy

with open(inputcsv, mode='r', encoding='utf-8') as infile, open(outputcsv, mode='w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()

    for row in reader:
        writer.writerow(row)
        modifiedrow = majorvariation(row)
        writer.writerow(modifiedrow)

print('CSV file created with major variation')
