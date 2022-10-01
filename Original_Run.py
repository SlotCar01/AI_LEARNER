# Hello! This is Katie, Lucas, and Carlos' AI Slot Car code, AI implemented! This is Rev 5 on 12/7/2021. Comments are by Katie Pype.
# Code is a collective effort from Katie, Lucas, and Carlos.
# This code below takes the TensorFlow Lite model we created out of Edge Impulse Project: AI Slot Car, Iteration 1 Rev 0 (currently private)
# From this model we imported, we have a few methods that will be explained in the code. These set up our pins on our 
# Raspberry Pi, capture the data in a way that makes sense for the model, and allows the model to spit out
# values we need in order to interpret correctly and have our DC driver either increase or decrease the PWM voltage signal. 
# Let's begin! 
import RPi.GPIO as GPIO # GPIO = Global Pin Input Output
import time
import board
import adafruit_bno055 # Our Euler angle and accelerometer
import busio
import numpy as np
import tflite_runtime.interpreter as tflite # Importing TFLite to not have to install TensorFlow as an entire package on the Pi.
# WARNING: It is EXTREMELY important that TensorFlow runs on 64-Bit OS and Python. Errors will flash and code WILL NOT WORK if ran on a 32-bit system.
# This is NOT mentioned on TensorFlow's website. It really should be, pretty important y'know. 
# The protocol I2C is utilized for our sensor board. All this needed was a 3.3VDC power source,
# then the SCL/SDA pins for transmitting and receiving. 

i2c = busio.I2C(board.SCL, board.SDA) # Activating the pins on the Pi for Tx/Rx data from an I2C sensor.
sensor = adafruit_bno055.BNO055_I2C(i2c) # Activating this protocol on the sensor board.
motor = 13 #This was a PWM pin on the Pi. This special pin was able to output a PWM value to the DRV8871 DC Drive.
# Below is the first method. This was to set up the pins on the Pi.
def setup():
    global pwm # PWM for sending those specific values to Pin 13 for the DC Driver.
    GPIO.setmode(GPIO.BCM) # 'BCM' was used if you're using only one Pi. If you use 'BOARD', it will change the values of the pins!
    GPIO.setup(motor, GPIO.OUT) # Set the motor as an output, as RPi pins can be set either/or Input or Output
    GPIO.output(motor, GPIO.LOW) # Don't need the dang motor running immediately at startup! Set this to LOW = 0 VDC.
    pwm = GPIO.PWM(motor, 100) # Utilizing the PWM library. Define the pin you're using and the range of speed it has.
    pwm.start(0) # We want the starting point to be 0! 0 = OFF or LOW. 
    GPIO.setwarnings(False) #This was an odd one. Got some interesting error messages, so we use this to turn those off. Do you need it? I don't know.
def loop():
    speed= 61 # This baseline is our speed if there is no corner. 
    curve_array= [] # Empty array for our structures data based on our real time inputs.
    while True:
        curve_array = capture (curve_array)
        for dc in range(0, speed, 10):  # Loop 0 to 61% of full RPM, stepping 10 steps each loop
            pwm.ChangeDutyCycle(dc)
            time.sleep(0.01)  # Hold 0.01 seconds at current RPM
        time.sleep(0.2), 
        for dc in range(speed, -1, -2): # Go from 61% to 0, decreasing by 2 steps each pulse.
            pwm.ChangeDutyCycle(dc)
            time.sleep(0.01)  # Hold 0.01 seconds at current RPM
        # print(curve_array) <==== Uncomment this to understand what length your curve array is!
        # By doing this, you can figure out how large your array is before it spits out a tensor output.
        # We counted ours to be 66 data points long, hence we wait until the length is 66 points long.
        # After that, the speed is determined by the curve array data going into the model.
        # The model then spits out three confidence ratings: Turn 1, Turn 2, Turn 3. 
        # These are decimals from 0.0 - 1.0 that is the percentage of confidence that the model thinks it's
        # in a specific turn. If that is above 50%, it will reduce the speed to that turn specified
        # in def learn_damn_you(). 
        if len(curve_array) == 66: # By printing out the curve 
            speed = learn_damn_you(curve_array) # Throwing the squeaky clean data into the model.
            time_stamp = 0 # resets our timestamp. May be unused as we are not collecting a timestamp for the AI model. Only data collection.
            curve_array = [] # Empties the array for the next set of tensors.
# This is our method for capturing all the data to input into our AI model. 
# This takes the raw sensor data from the BNO055 (both acceleration and Euler) and organizes it carefully into an array
# so that TensorFlow Interpreter is able to analyze it. This is extremely important, since our model was based on 
# 6 values: X, Y, Z from the accelerometer, and eX, eY, and eZ from the Euler angle. 
# We must make sure the data being fed in raw form is processed to look exactly like the .csv files we originally used to capture the data.
def capture(curve_array): # This is adding the current list of 6 values to the running list for the curve array
    raw_data = (sensor.acceleration, sensor.euler) # Using the two sensors from the BNO055
    # Below is where the data is structured to emulate our .csv files for our model to interpret it correctly.
    # The sensor data comes in as tuples. These tuple values need to be organized and re-structured as an array.
    # The first 0 = accelerometer. [0][0] = Accelerometer, X-axis. [1] in the first brackets = Euler. Ex. [1][1] = Euler, eY axis.
    structured_data= (raw_data[0][0], raw_data[0][1], raw_data[0][2], raw_data[1][0], raw_data[1][1], raw_data[1][2]) 
    # The for loop below is cleaning up the data.
    for i in range(len(structured_data)): 
        curve_array.insert(-1, structured_data[i])
    return curve_array

# Next! This is where the magic happens. Magic, or, AI. Whichever sounds better.
# This method is where TensorFlow Lite and our model get implemented. TensorFlow's 'interpreter' takes the input data we cleaned up,
# and throws it at the model after putting it into an array.
def learn_damn_you(data):
    curve1 = 60 #Defined Curve 1 as the first turn from the starting line.
    curve2 = 60
    curve3 = 60 # These values indicate the PWM value that it's assigned to if recognized as a corner.
    interpreter = tflite.Interpreter(model_path="slotcar.tflite") #Our model! Remember to keep it in the same folder
    # Or else it will not be found.
    interpreter.allocate_tensors() #Pre-allocates tensors before inference or execution. Not optional!
    i_details = interpreter.get_input_details() 
    o_details = interpreter.get_output_details()

    input_shape = i_details[0]['shape']
    # print(np.array(np.asarray(data))) Print to see your inputs and determine array size!
    # This is where numpy comes into play. Numpy arranges all that cleaned data into an array
    # and set it as a float so that that data can be set into tensors for the model. 
    input_data = np.array([np.asarray(data),], dtype=np.float32) #Sets the data into float32 if they were not before.
    interpreter.set_tensor(i_details[0]['index'], input_data) # Uses the cleaned array to set the tensors. 
    interpreter.invoke() # Awaken the beast! This activates the interpreter. All the above was to 
    # simply make sure the data is scrubbed, cleaned, organized, set, and 'tensor-ed' before this function.
    # Make sure no other objects are called upon at the same time as this is very process heavy.
    # This is where we join our AI data into real life results. 
    # The 'if' and 'elif' statements are for the output data.
    # The output_data spits out a 2 x 3 tensor. This is the AI's confidence on if it think it's in Turns 1,2, or 3.
    # If the AI is more than 50% confident (.5 in this case),
    # It will modify it's speed based on Curve 1-3. 
    # Otherwise, it will return back to its base speed.
    output_data = interpreter.get_tensor(o_details[0]['index']) #This returns a tensor of 2x3 values.
    # print(output_data)
    if output_data[0][0] >.5: 
        print ("curve 1")
        return curve1
    elif output_data[0][1] >.5:
        print ("curve 2")
        return curve2
    elif output_data[0][2] >.5:
        print ("curve 3")
        return curve3
    else:
        return 55
#  This is very important below!! This clears the GPIO pin and allows it to reset back to 0.
#  Otherwise, when program quits the pins goes HIGH and runs rampant.
def destroy():
    pwm.stop()
    GPIO.output(motor, GPIO.LOW)
    GPIO.cleanup()
# Finally, the main loop. All 5 lines of it. It runs the setup on the Pi pins
# Next comes the main loop that it loops around in forever, until!
# DESTROY!...Or it loses power. Either or.
if __name__ == '__main__':
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
