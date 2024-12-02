# OTA Service Setup Guide

---

## Part 1: Server Configuration

1. **Clone Repository**  
   Open Terminal and run:
```bash
git clone https://github.com/Exsinnot/OTA.git
```
2. **Move Server Folder**  
Move the `Server` folder to the desired server machine.

3. **Install Dependencies**  
Run the following command in Terminal:
```bash
pip install flask flask-socketio flask-cors
```
4. **Start the Server**  
Navigate to the `Server` folder and run:
```bash
cd Server python3 app.py
```
*(Use `python` instead of `python3` for Python versions below 3.)*

6. **Open Port 5000 on the Firewall**  
Example command:
```bash
ufw allow 5000
```
---

## Part 2: Client Configuration on Raspberry Pi

1. **Install Tools and Dependencies**  
Run:
```bash
sudo apt install -y git build-essential libtool autoconf libusb-1.0-0-dev pkg-config automake
```
2. **Clone OpenOCD Repository**  
Run:
```bash
git clone https://github.com/raspberrypi/openocd.git
cd openocd
./bootstrap
./configure --enable-sysfsgpio --enable-bcm2835gpio
make -j$(nproc)
sudo make install
```
3. **Configure Raspberry Pi GPIO SWD**  
Create and edit the configuration file: sudo nano /usr/local/share/openocd/scripts/interface/raspberrypi_swd.cfg
 

```bash
Add the following content:  
adapter driver bcm2835gpio 
adapter gpio swclk 25 
adapter gpio swdio 24 
adapter gpio srst 18 
transport select swd
```
---

## Part 3: Install Client Files

Move the `Client` folder to the Raspberry Pi in any desired location.

---

## Part 4: Configure Auto Run for OTA Service

1. **Create a Service File**  
Run:  
```bash
sudo nano /etc/systemd/system/ota_semi.service
```
Add the following content:  

```bash
[Unit] 
Description=OTA Semi Service 
After=network.target 
 
[Service] 
ExecStart=/usr/bin/python /home/user/RV/OTA_semi.py 
Restart=always 
RestartSec=3 
User=user 
Group=user 
WorkingDirectory=/home/user/RV 
Environment=PYTHONUNBUFFERED=1 
 
[Install] 
WantedBy=multi-user.target
```
2. **Modify Paths**  
- **Python Path:** `/usr/bin/python`  
- **OTA Program Path:** `/home/user/RV/OTA_semi.py`  
- **Working Directory:** `/home/user/RV`

3. **Save and Reload Systemd**  
Run:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ota_semi.service
sudo systemctl start ota_semi.service
```

---

## OTA Service Usage

1. **Connect Wiring**  

| **Raspberry Pi** | **STM32F767ZI** |
|------------------|-----------------|
| GPIO25           | SWCLK           |
| GPIO24           | SWDIO           |
| GND              | GND             |

2. **Test Connection**  
Run the following command on the Raspberry Pi:  
```bash
sudo openocd -f interface/raspberrypi_swd.cfg -f target/stm32f7x.cfg
```
- If it **hangs at `interface`**, the connection is successful.  
- If errors occur, the connection is faulty.

3. **Configure `config.json` in Client Folder**  
Update the `IP` to match the server's IP and port.  
Example:  

```json
{
    "IP": "http://192.168.0.0:1234"
}
```
