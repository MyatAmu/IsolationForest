import pandas as pd
import mysql.connector
from sklearn.preprocessing import MinMaxScaler

dbconnect = mysql.connector.connect(
    host = 'localhost',
    user =  'root1',
    password =  'root1',
    database =  'fortytwo'
)
cursor = dbconnect.cursor()

query = """SELECT userID, IPaddress, Timezone, Latitude, Longitude, DeviceInfo, TypingSpeed, MouseSpeed, LoginTime FROM useractivity"""

cursor.execute(query)
data = cursor.fetchall()

cursor.close()
dbconnect.close()

columns = ['userID', 'IPaddress', 'Timezone', 'Latitude', 'Longitude', 'DeviceInfo', 'TypingSpeed', 'MouseSpeed', 'LoginTime']
df = pd.DataFrame(data, columns=columns)

df.fillna({'Latitude': 0, 
           'Longitude': 0, 
           'TypingSpeed' : df['TypingSpeed'].median(),
           'MouseSpeed': df['MouseSpeed'].median(),
           'Timezone': 'UTC',
           'DeviceInfo': 'Unknown'}, inplace=True)

df.to_csv('useractivity.csv', index=False)

print('CSV file created')