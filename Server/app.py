import threading
import time
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask import Flask, request, jsonify, send_from_directory, render_template
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
CORS(app)
socketio = SocketIO(app)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

connected_clients = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist('files[]')
    saved_files = []

    for file in files:
        if file.filename == '':
            continue

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        saved_files.append(file.filename)

    return jsonify({"message": "Files uploaded successfully", "files": saved_files}), 200

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": f"File {filename} deleted"}), 200
    return jsonify({"error": "File not found"}), 404

@app.route('/files', methods=['GET'])
def list_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify({"files": files, "listMC_Online": connected_clients}), 200

@app.route('/upload_code_to_mc', methods=['GET'])
def upload_code_to_mc():
    mc_name = request.args.get('mc_name')
    code_file = request.args.get('code_file') 

    if mc_name in connected_clients:
        sid = connected_clients[mc_name][0] 
        socketio.emit('receive_message', {'command': "update", 'file': code_file}, room=sid)
        return jsonify({"status": "success", "message": f"Update command sent to {mc_name}"}), 200
    else:
        return jsonify({"status": "error", "message": f"{mc_name} is not connected"}), 404

@app.route('/editHostName', methods=['GET'])
def editHostName():
    mc_name = request.args.get('mc_name')
    newName = request.args.get('NewName') 

    if mc_name in connected_clients:
        sid = connected_clients[mc_name][0] 
        socketio.emit('receive_message', {'command': "ReHostName", 'HostName': newName}, room=sid)
        return jsonify({"status": "success", "message": f"Update command sent to {mc_name}"}), 200
    else:
        return jsonify({"status": "error", "message": f"{mc_name} is not connected"}), 404


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@socketio.on('send_name')
def handle_name(data):
    name = data.get('name')
    if name:
        if not (name in connected_clients):
            connected_clients[name] = [request.sid ,time.time() ] 
            print(f"Raspberry Pi {name} connected")
        elif connected_clients[name][0] != request.sid:
            count = 0
            newName = "Default"+str(count)
            while newName in connected_clients:
                count += 1
                newName = "Default"+str(count)
            socketio.emit('receive_message', {'command': "ReHostName", 'HostName': newName}, room=request.sid)

@socketio.on('send_message')
def handle_message(data):
    pi_name = data['name'] 
    command = data['command']
    print(pi_name)
    print(connected_clients[pi_name])
    if pi_name in connected_clients:
        sid = connected_clients[pi_name]
        emit('receive_message', {'command': command}, room=sid)
    else:
        emit('receive_message', {'response': f'{pi_name} is not connected'})

@socketio.on('getdisplay')
def handle_client_message(data):
    print(f"Received from Raspberry Pi: {data}")
    emit('message_from_pi', {'message': data}, broadcast=True)

# ฟังก์ชันที่ใช้ลบชื่อเครื่องที่ไม่ได้ส่งชื่อซ้ำภายใน 5 วินาที
def remove_inactive_clients():
    while True:
        time.sleep(5)  # ตรวจสอบทุกๆ 5 วินาที
        current_time = time.time()
        to_remove = []
        
        for name,last_activity in list(connected_clients.items()):
            if current_time - last_activity[1] > 7:  # ถ้าเครื่องไม่ได้ติดต่อมาเกิน 5 วินาที
                to_remove.append(name)

        # ลบเครื่องที่ไม่ได้ติดต่อ
        for name in to_remove:
            del connected_clients[name]
            print(f"Disconnected {name} due to inactivity.")

# ฟังก์ชันนี้จะเริ่มทำงานใน background thread
def start_inactivity_check():
    threading.Thread(target=remove_inactive_clients, daemon=True).start()

if __name__ == '__main__':
    start_inactivity_check()  # เริ่มฟังก์ชันตรวจสอบการใช้งาน
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
