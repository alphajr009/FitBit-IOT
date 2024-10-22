from flask import Flask, jsonify, render_template
import time
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# Store the steps, user details, fall detection, and MQTT status
step_data = {
    "steps": 0,
    "total_steps_10s": 0,
    "total_steps_overall": 0,
    "fall_detected": False,
    "mqtt_status": "Disconnected",
    "last_reset": time.time()
}

# MQTT broker settings
MQTT_BROKER = "5f474025409c4b7588c11fbc1c3dffcb.s1.eu.hivemq.cloud"
MQTT_PORT = 8884  # WebSocket port
MQTT_TOPIC = "esp32/stepcounter"
MQTT_USER = "hivemq.webclient.1729593331255"
MQTT_PASS = "QoS@.4Obqk983V,:xBKa"

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

    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        step_data["mqtt_status"] = "Connected"
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def mqtt_subscribe():
    client = mqtt.Client(transport="websockets")
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get-activity', methods=['GET'])
def get_activity():
    return jsonify({
        "steps": step_data["total_steps_overall"],
        "fall_detected": step_data["fall_detected"],
        "mqtt_status": step_data["mqtt_status"]
    })

if __name__ == '__main__':
    mqtt_subscribe()
    app.run(host='0.0.0.0', port=5000)
