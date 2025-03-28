import csv
import random
from datetime import datetime, timedelta

inputcsv = 'useractivity.csv'
outputcsv = 'useractivityvariation.csv'

def introducevariation(row):
    rowcopy = row.copy()

    rowcopy["Latitude"] = float(row["Latitude"]) + round(random.uniform(-0.05, 0.05), 6)
    rowcopy["Longitude"] = float(row["Longitude"]) + round(random.uniform(-0.05, 0.05), 6)
    
    newTypingSpeed = int(row["TypingSpeed"]) + random.randint(-5, 5)
    rowcopy["TypingSpeed"] = max(10, min(200, newTypingSpeed))

    newMouseSpeed = float(row["MouseSpeed"]) + random.randint(-50, 50)
    rowcopy["MouseSpeed"] = max(200, min(2000, newMouseSpeed))

    originaltime = datetime.strptime(row["LoginTime"], '%Y-%m-%d %H:%M:%S')
    timevariation = timedelta(hours=random.randint(1, 3), seconds=random.randint(-60, 60))
    rowcopy["LoginTime"] = (originaltime + timevariation).strftime('%Y-%m-%d %H:%M:%S')

    return rowcopy

with open(inputcsv, mode='r', encoding='utf-8') as infile, open(outputcsv, mode='w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()

    for row in reader:
        writer.writerow(row)
        modifiedrow = introducevariation(row)
        writer.writerow(modifiedrow)

print('CSV file created with variation')
