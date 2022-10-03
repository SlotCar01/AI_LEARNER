#Run a single lap and capture accelorometer data

import RPi.GPIO as GPIO # GPIO = Global Pin Input Output
import time
import board
import math
import adafruit_bno055 # Our Euler angle and accelerometer
import busio
import numpy as np
import csv

run_name = "run1.csv"
api_key='ei_238fae...'
min_points = 12 #the minimum number of data points need by edge impulse to classify a feature.

i2c = busio.I2C(board.SCL, board.SDA) # Activating the pins on the Pi for Tx/Rx data from an I2C sensor.
sensor = adafruit_bno055.BNO055_I2C(i2c) # Activating this protocol on the sensor board.
motor = 13 #This was a PWM pin on the Pi. This special pin was able to output a PWM value to the DRV8871 DC Drive.
battery = 18
# Below is the first method. This was to set up the pins on the Pi.
def setup():
    global pwm # PWM for sending those specific values to Pin 13 for the DC Driver.
    global data_points = 0 #varible for counting how many data points are colllected in lab
    GPIO.setmode(GPIO.Board) # 'BCM' was used if you're using only one Pi. If you use 'BOARD', it will change the values of the pins!
    GPIO.setup(motor, GPIO.OUT) # Set the motor as an output, as RPi pins can be set either/or Input or Output
    GPIO.output(motor, GPIO.LOW) # Don't need the dang motor running immediately at startup! Set this to LOW = 0 VDC.
    GPIO.setup(battery, GPIO.IN)
    pwm = GPIO.PWM(motor, 100) # Utilizing the PWM library. Define the pin you're using and the frequency of the pulse
    #Change in the pulse frequency. The faster the slot car pulse the faster the car goes 
    pwm.start(0) #The starting duty cycle so the car will only drive when it detects voltage coming from the track
    GPIO.setwarnings(False) #This was an odd one. Got some interesting error messages, so we use this to turn those off. Do you need it? I don't know.
    
def capture(curve_array, start): # This is adding the current list of 6 values to the running list for the curve array
    raw_data = (sensor.acceleration, sensor.euler) # Using the two sensors from the BNO055
    current_time = time.time()
    time_stamp = round(current_time-start, 1)
    # Below is where the data is structured to emulate our .csv files for our model to interpret it correctly.
    # The sensor data comes in as tuples. These tuple values need to be organized and re-structured as an array.
    # The first 0 = accelerometer. [0][0] = Accelerometer, X-axis. [1] in the first brackets = Euler. Ex. [1][1] = Euler, eY axis.
    structured_data= (time_stamp, raw_data[0][0], raw_data[0][1], raw_data[0][2], raw_data[1][0], raw_data[1][1], raw_data[1][2]) 
    # The for loop below is cleaning up the data.
    for i in range(len(structured_data)): 
        curve_array.insert(-1, structured_data[i])
    return curve_array

def loop():
    speed= 61 #starting speed of the car to safely make it around the track
    curve_array= [] # Empty array for our structures data based on our real time inputs.
    if (GPIO.input(battery): #check if car is connected to the track if so
        start_time = time.time()
        pwm.ChangeDutyCycle(speed) #turn the car on
        while (GPIO.input(battery): #run the first lap as long as the car is not on battery
               data_points += 1 
               curve_array = capture (curve_array, start_time) #Not needed for this part, capture data that the car and edge impulse will use
               time.sleep(0.2) #simulate other calculation the car will do in later stages
    elif (data_points != 0): #ran the lap and gathered the data
        pwm.ChangeDutyCycle(0) #turn the car off
        curves =  math.floor(data_points/min_points) #how many curves were gathered
        for n in range(curves): #devide out the base level to each bucket in the curve
               curve[n]= min_points
               data_points -= min_points
        while (data_points > 0): #evenly distribute the remainer of the data points to the buckets
               for m in range (curves):
                    if (data_points > 0):
                        curve[m] += 1
                        data_points -= 1
        with open(run_name, 'wb') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow(['Time stamp', 'accX', 'accY','accZ','eularX', 'eularY','eularZ', 'curve']) #header
            c=0
            for i in range(curves):  #convert the array to csv
               for j in range(curve[i]):
                  filewriter.writerow([curve_array[c][0], curve_array[c][1], curve_array[c][2],curve_array[c][3],curve_array[c][4], curve_array[c][5],curve_array[c][6], i])
                  c += 1
        csvfile.close()
               
        with open(run_name, 'r') as file:
            res = requests.post(url='https://ingestion.edgeimpulse.com/'+api_key+'/training/data',
            data=file,
            headers={
                 'Content-Type': 'application/cbor',
                 'x-file-name': 'idle.01',
                 'x-label': 'idle',
                 'x-api-key': api_key,
                        })

            if (res.status_code == 200):
                print('Uploaded file to Edge Impulse', res.status_code, res.content)
            else:
                print('Failed to upload file to Edge Impulse', res.status_code, res.content)
        print("The lap has been uploaded " )
        time.sleep(5)
    else : #annoy the pit crew
        print ("Can we get a move on?!")
        time.sleep(5)

#  This is very important below!! This clears the GPIO pin and allows it to reset back to 0.
#  Otherwise, when program quits the pins goes HIGH and runs rampant. 
def destroy():
    pwm.stop()
    GPIO.output(motor, GPIO.LOW)
    GPIO.cleanup()
               
if __name__ == '__main__':
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
