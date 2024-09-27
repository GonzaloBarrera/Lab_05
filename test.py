from datetime import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import config
import json
import time
import ADC0832
import math

# Thermistor Data
BETA_COEFFICIENT = 3380
NOMINAL_RESISTANCE = 10000
ADC_MAX_VALUE = 255
VREF = 3.3

# Start ADC
ADC0832.setup()

# User-specified callback function
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

# Configure the MQTT client
myMQTTClient = AWSIoTMQTTClient(config.CLIENT_ID)
myMQTTClient.configureEndpoint(config.AWS_HOST, config.AWS_PORT)
myMQTTClient.configureCredentials(config.AWS_ROOT_CA, config.AWS_PRIVATE_KEY, config.AWS_CLIENT_CERT)
myMQTTClient.configureConnectDisconnectTimeout(config.CONN_DISCONN_TIMEOUT)
myMQTTClient.configureMQTTOperationTimeout(config.MQTT_OPER_TIMEOUT)

# Connect to MQTT Host
if myMQTTClient.connect():
    print('AWS connection succeeded')

# Subscribe to topic
myMQTTClient.subscribe(config.TOPIC, 1, customCallback)
time.sleep(2)

def get_photoresistor_value():
    return ADC0832.getADC(1)

def get_thermistor_value():
    res = ADC0832.getADC(0)
    Vr = VREF * float(res) / ADC_MAX_VALUE
    Rt = NOMINAL_RESISTANCE * Vr / (VREF - Vr)
    temp_K = 1 / (((math.log(Rt / NOMINAL_RESISTANCE)) / BETA_COEFFICIENT) + (1 / (273.15 + 25)))
    temp_C = round(temp_K - 273.15, 2)
    return temp_C

# Loop to collect data and publish
try:
    while True:
        photoresistor_value = get_photoresistor_value()
        thermistor_value = get_thermistor_value()

        payload = json.dumps({
            "photoresistor": photoresistor_value,
            "thermistor_celsius": thermistor_value
        })

        myMQTTClient.publish(config.TOPIC, payload, 1)
        print(f"Published: {payload} to {config.TOPIC}")

        time.sleep(10)

except KeyboardInterrupt:
    ADC0832.destroy()
    print('Program terminated')
