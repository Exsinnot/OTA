import socketio
import requests
import subprocess
import json
config = None
with open('config.json', 'r') as file:
    config = json.load(file)


sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server")
    sio.emit('send_name', {'name': config['HostName']})

@sio.event
def receive_message(data):
    global command,config
    commandtemp = data.get('command')
    command = commandtemp
    print(commandtemp)
    if command == "update":
        print("UPDATE")
        filename = data.get('file')
        try:
            response = requests.get(f"{config['IP']}/download/{filename}", stream=True)

            if response.status_code == 200:
                if filename.split(".")[1] == "bin":
                    code_filename = "code.bin"
                else:
                    code_filename = "code.hex"
                with open(code_filename, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192): 
                        file.write(chunk)
                openocd_command = [
                "openocd",
                "-f", "interface/raspberrypi_swd.cfg",
                "-f", "target/stm32f7x.cfg",
                "-c", "adapter speed 100",
                "-c", "init",
                "-c", "halt",
                "-c", "flash erase_address 0x08000000 0x10000",
                "-c", f"program {code_filename} 0x08000000 verify",
                "-c", "reset run",
                "-c", "exit"
            ]
                try:
                    subprocess.run(openocd_command, check=True)
                    print("OpenOCD command executed successfully.")
                except subprocess.CalledProcessError as e:
                    print(f"Error during execution: {e}")
            else:
                print(f"Failed to download file. HTTP Status Code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred: {e}")
                
            print(f"Received message: {data.get('command')}")
    elif command == "ReHostName":
        config['HostName'] = data.get('HostName')
        with open('config.json', 'w') as file:
            json.dump(config, file)
        
@sio.event
def connect_error(data):
    print("Connection failed:", data)

@sio.event
def disconnect():
    print("Disconnected from server")

try:
    sio.connect(config['IP'])
    while True:
        sio.sleep(5)
        sio.emit('send_name', {'name': config['HostName']})
except Exception as e:
    sio.disconnect()
    print(f"WebSocket Error: {e}")
