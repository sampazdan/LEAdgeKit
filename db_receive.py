#COPYRIGHT 2023 - Brookgreen Technologies
#Modification, redistribution, and use of this software is 
#strictly prohibited unless direct written consent 
#is provided by Brookgreen Technologies

#This code is designed to be used with a Congatec SA7 SMARC module 
#to connect to a STM32 microcontroller.
#The data registers (6 inputs) on the STM32 are read via serial interface.
#The input register status data is parsed into bits and if inputs 
#have been triggered from HIGH to LOW 
#a UTC datestamp will be stored in a Postgres database alogn with deviceId


#Required packages
import serial
import sys
import time
import psycopg2
from datetime import datetime
import getpass

#Global Variables
#Message packet header for requesting data from STM32
# SUC_COMM_HEADER = bytes([0xab, 0xfd])
#Message packet header when using MODBUS
SUC_COMM_HEADER = bytes([0xaa, 0x01, 0x06])
#Request message for getting input data from STM32
GET_DATA_MESSAGE = [0xaa, 0x01, 0x00, 0x06]
#Timer deley between read cycles
WAIT_DELAY = .001
#Postgres DB Connection Config
PARAMS = {
    'user': "",
    'password': "",
    'host': 'localhost',
    'port': '5432',
    'dbname': 'leadge'
}
#CONNECTION_CONFIG = "dbname = 'leadge' user='samtest' host='localhost' port=5432 password = 'samtest'"
#Serial device identifier - defaults to USB serial adapter - change with arg1 on exec
DEVICE = "/dev/ttyS4"
#BAUD rate over which to communicate - defaults to 115.2 Kbaud
BAUD = 115200

#Initialize communications with STM32 chip and database
def init_com():
    #Create global com variable used in other methods for communications with STM32 chip
    global com
    #Connect to serial port
    com = serial.Serial(DEVICE, BAUD)

    #Build a command to create MeterEvents table if needed
    cursor.execute('CREATE TABLE IF NOT EXISTS MeterEvents (\
        id SERIAL PRIMARY KEY,\
        datestamp timestamp,\
        deviceid int\
    )')

    #Commit any execute statements currently in the cursor
    connection.commit()

def connect():
    global connection
    connection = psycopg2.connect(**PARAMS)
    connection.autocommit = True
    global cursor
    cursor = connection.cursor()

#Method to detect "cliff" at END of input trigger
def detect_high_to_low(byte, prev):
    #Check incoming byte against previous to detect changes using XOR
    change = byte ^ prev
    #BITWISE check for cliffs across entire byte (all 6 inputs) using AND
    high_to_low = change & prev
    
    #Method storage for device ids of triggered devices
    devicesTriggered = []

    #If no cliffs detected for any inputs then return empty array
    if high_to_low == 0:
        return devicesTriggered
    #Cliffs detected, then find and return array of specifically affected inputs  
    else:
        #For all inputs 
        for i in range(0,8):
            #BITWISE calc for specific input to determine if change is FALL OFF cliff at END of trigger cycle
            if high_to_low & (2 ** i):
                #Store device Id for output
                devicesTriggered.append(i)
        #Return ID list of triggered devices
        return devicesTriggered

#Store device trigger data datestamp in Postgres
def create_db_entry(triggeredDevices):
    #For each triggered device id found in "detect_high_to_low"
    for deviceId in triggeredDevices:    
        #Create INSERT statement to put data into Postgres    
        statement = f'INSERT INTO MeterEvents (datestamp, deviceid) VALUES (\'{datetime.utcnow()}\', {deviceId})'
        #Queue the statement execution
        cursor.execute(statement)
    #Execute and commit insert statements to the Postgres DB
    connection.commit() 

#An open loop method for requesting and receiving INPUT register status from the STM32 chip
def get_com_data():

    byte = prev = 0x0

    try:
        while True:

            recv = bytes([0x00, 0x00, 0x00])
            while recv[:3] != SUC_COMM_HEADER:
                recv = com.read(5)
                time.sleep(WAIT_DELAY)

            prev = byte
            byte = recv[3]
            byte = ~byte & 0xFF

            flipped = detect_high_to_low(byte, prev)

            if len(flipped) != 0:
                print(f"Meter pulse detected! {flipped}")
                create_db_entry(flipped)

    except:
        com.flush()

def pg_login():

    logged = False

    while not logged:
        PARAMS['user'] = input("Postgres Username: ")
        PARAMS['password'] = getpass.getpass("Postgres Password: ")

        try:
            connect()
        except:
            print("Authentication failed. Please try again.")
            continue
        
        print(f"Now logged in as user {PARAMS['user']}.")
        print("----------------------------------------------------------------")
        logged = True

#Main code laucnh
if __name__ == "__main__":
    #Read command line args - arg 1 for device, arg 2 for baud
    if len(sys.argv) != 3:
        print(f"Defaulting to comms over {DEVICE} at {BAUD} baud")
    else:
        DEVICE = sys.argv[1]
        BAUD = sys.argvq[2]
    #Initialize communications with STM32 chip and Postgres Database
    pg_login()
    init_com()
    #Start loop for sending data request message and listening for responses
    get_com_data()
