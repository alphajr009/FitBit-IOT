from flask import Flask, jsonify, render_template
import time
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# Store the steps, user details, fall detection, and WiFi status
step_data = {
    "steps": 0,  # Current step count (received from ESP32 via MQTT)
    "total_steps_10s": 0,  # Steps in the current 10-second window (for activity classification)
    "total_steps_overall": 0,  # Total accumulated steps over time
    "fall_detected": False,  # Fall detection status
    "age": None,
    "gender": None,
    "activity": "Not Moving",
    "wifi_status": "Disconnected",  # Default WiFi status
    "mqtt_status": "Disconnected",  # MQTT connection status
    "last_reset": time.time()
}

# MQTT broker settings
MQTT_BROKER = "5f474025409c4b7588c11fbc1c3dffcb.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_TOPIC = "esp32/stepcounter"
MQTT_USER = "alphawefit"
MQTT_PASS = "Alpha@2024"

# Activity classification logic based on step count
def classify_activity(step_count):
    if step_count == 0:
        return "Not Moving"
    elif step_count <= 10:
        return "Walking"
    elif step_count <= 20:
        return "Jogging"
    else:
        return "Running"

# MQTT message handling function (called when a message is received)
def on_message(client, userdata, message):
    global step_data
    print(f"Message received: {message.payload.decode()}")
    try:
        step_info = json.loads(message.payload.decode())
        step_data["steps"] = step_info.get("steps", 0)
        step_data["fall_detected"] = step_info.get("fall_detected", False)

        # Update step data
        step_data["total_steps_overall"] += step_data["steps"]
        step_data["total_steps_10s"] += step_data["steps"]

        # Check if 10 seconds have passed and classify activity
        if time.time() - step_data["last_reset"] >= 10:
            step_data["activity"] = classify_activity(step_data["total_steps_10s"])
            step_data["total_steps_10s"] = 0
            step_data["last_reset"] = time.time()

    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# MQTT connection handling
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        step_data["mqtt_status"] = "Connected"  # Update MQTT status immediately
        client.subscribe(MQTT_TOPIC)
    else:
        print("Failed to connect, return code %d\n", rc)

# Initialize the MQTT client and connect to the broker
def mqtt_subscribe():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()  # Enable SSL/TLS for secure connection
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint to get the current activity, total step count, fall detection, and MQTT status
@app.route('/api/get-activity', methods=['GET'])
def get_activity():
    return jsonify({
        "steps": step_data["total_steps_overall"],
        "activity": step_data["activity"],
        "fall_detected": step_data["fall_detected"],
        "mqtt_status": step_data["mqtt_status"]
    })

if __name__ == '__main__':
    mqtt_subscribe()
    app.run(host='0.0.0.0', port=5000)
