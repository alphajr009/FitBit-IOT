from flask import Flask, jsonify, render_template
import time
import paho.mqtt.client as mqtt
import mysql.connector
import json

app = Flask(__name__)

# Database connection
db_connection = mysql.connector.connect(
    host="auth-db1666.hstgr.io",  # Your MySQL database host
    user="u663312418_alpha",      # Your MySQL database username
    password="tRbvr4;Tl2", # Your MySQL database password
    database="u663312418_fitbit"  # Your MySQL database name
)
db_cursor = db_connection.cursor()

# Store the steps, fall detection, and MQTT status
step_data = {
    "steps": 0,
    "fall_detected": False,
    "mqtt_status": "Disconnected",
    "activity": "Not Moving",
}

# MQTT broker settings
MQTT_BROKER = "5f474025409c4b7588c11fbc1c3dffcb.s1.eu.hivemq.cloud"
MQTT_PORT = 8884  # WebSocket port
MQTT_TOPIC = "esp32/stepcounter"
MQTT_USER = "hivemq.webclient.1729593331255"
MQTT_PASS = "QoS@.4Obqk983V,:xBKa"

# Activity classification based on steps count rate
def classify_activity(step_count):
    if step_count == 0:
        return "Not Moving"
    elif step_count <= 10:
        return "Walking"
    elif step_count > 10:
        return "Running"
    return "Not Moving"

# MQTT message handling function
def on_message(client, userdata, message):
    global step_data
    print(f"Message received: {message.payload.decode()}")
    try:
        step_info = json.loads(message.payload.decode())
        step_data["steps"] = step_info.get("steps", 0)
        step_data["fall_detected"] = step_info.get("fall_detected", False)

        # Classify the current activity
        step_data["activity"] = classify_activity(step_data["steps"])

        # Insert the data into the database
        sql = "INSERT INTO steps_data (step_count, fall_detected, activity) VALUES (%s, %s, %s)"
        db_cursor.execute(sql, (step_data["steps"], step_data["fall_detected"], step_data["activity"]))
        db_connection.commit()

    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# MQTT connection handling
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

# Retrieve daily step count from the database
def get_daily_steps():
    db_cursor.execute("SELECT SUM(step_count) FROM steps_data WHERE DATE(created_at) = CURDATE()")
    result = db_cursor.fetchone()
    return result[0] if result[0] else 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get-activity', methods=['GET'])
def get_activity():
    daily_steps = get_daily_steps()
    return jsonify({
        "steps": step_data["steps"],
        "fall_detected": step_data["fall_detected"],
        "mqtt_status": step_data["mqtt_status"],
        "activity": step_data["activity"],
        "daily_steps": daily_steps
    })

if __name__ == '__main__':
    mqtt_subscribe()
    app.run(host='0.0.0.0', port=5000)
