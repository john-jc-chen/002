import serial_rx_tx
import time
import sys
import re
import os
#import logging
from datetime import datetime

import _thread

logFile = None
write_able = False

username = "ADMIN"
passwd = "ADMIN"
new_passwd = ''
comport = "COM5"
baudrate = "9600"
bootloader = ""
firmware = ""
customer = ""
IP = ''
config_file = sys.argv[1]
f = open(config_file, 'r')
#of = open("command_log.txt", 'w')
commands = f.readlines()

for comm in commands:
    if comm.startswith("COM Port:"):
        comport = comm[9:].rstrip()
    elif comm.startswith("Baud Rate:"):
        baudrate = comm[10:].rstrip()
    else:
        pass
f.close()
serialPort = serial_rx_tx.SerialPort()

def OnReceiveSerialData():
    time.sleep(1.0)
    while serialPort.serialport.in_waiting > 0:
        print(serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8"))
        time.sleep(1.0)
def OpenCommand():
    global comport
    global baudrate
    serialPort.Open(comport,baudrate)
    print("COM Port Opened\r\n")

def login(username, passwd):
    serialPort.Send("")
    time.sleep(0.5)
    data = serialPort.serialport.readline().decode("utf-8", errors='ignore')
    while 'login:' not in data:
        print(data)
        data = serialPort.serialport.readline().decode("utf-8", errors='ignore')
    print(data)
    time.sleep(2.0)
    serialPort.Send(username)
    time.sleep(0.5)
    data = serialPort.serialport.readline().decode("utf-8", errors='ignore')
    print(data)
    serialPort.Send(passwd)
    time.sleep(1.0)
    data = serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8", errors='ignore')
    print(data)
    if "SMIS#" not in data:
        print("Failed to login with the password \"" + passwd + "\"\n Leave scrip!!!")
        serialPort.Close()
        sys.exit()
    #data = serialPort.serialport.read(serialPort.serialport.inWaiting())
    #print(data)

def logout():
    str = "exit\r"
    serialPort.serialport.write(str.encode("utf-8"))
    time.sleep(1.0)

def writeCommand(command):
    serialPort.Send(command)
    time.sleep(0.5)

def SetNetwork(IP, TFTP):
    serialPort.Send_raw('q')
    OnReceiveSerialData()
    backspace = bytearray([8 for i in range(20)])
    serialPort.serialport.write(backspace)
    time.sleep(0.5)
    OnReceiveSerialData()
    serialPort.Send(IP)
    OnReceiveSerialData()
    serialPort.Send("")
    OnReceiveSerialData()
    serialPort.Send("")
    OnReceiveSerialData()
    serialPort.serialport.write(backspace)
    time.sleep(0.5)
    serialPort.Send(TFTP)
    OnReceiveSerialData()
    serialPort.Send("y")
    OnReceiveSerialData()

def write_log(serial_number, message):
    if os.name == 'posix':
        log_dir = os.getcwd() + '/log'
    else:
        log_dir = os.getcwd() + "\\log"
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    if os.name == 'posix':
        file_name =log_dir + '/' + serial_number
    else:
        file_name =log_dir + "\\" + serial_number
    # logging.basicConfig(filename=file_name,level=logging.INFO, format='%(asctime)s - %(message)s', datefmt = '%d-%b-%y %H-%M-%S')
    # logging.info(message)
    # logging.shutdown()
    with open(file_name, 'w') as f:
        f.write("{}\n {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), message))



OpenCommand()
if serialPort.IsOpen():
    #serialPort.Send("")
    while True:
        time.sleep(2.0)
        while serialPort.serialport.in_waiting > 0:
            message = serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8", errors='ignore')
            print(message)
            message = message.rstrip()
            if " MBM-XEM-002 Boot Menu " in message:
                start_time = time.time()
                serialPort.Send_raw(" ")
                f = open(config_file, 'r')
                commands = f.readlines()
                i = 0
                for comm in commands:
                    if comm.startswith("User Name:"):
                        username = comm[10:].rstrip()
                    elif comm.startswith("New Password:"):
                        new_passwd = comm[13:].rstrip()
                        #commands[i]="New Password:\n"
                    elif comm.startswith("IP:"):
                        IP = comm[3:].rstrip()
                    elif comm.startswith("TFTP:"):
                        TFTP = comm[5:].rstrip()
                    elif comm.startswith("Bootloader Name:"):
                        strarry = comm.rstrip().split(':')
                        bootloader = strarry[1]
                    elif comm.startswith("Firmware Name:"):
                        firmware = comm[14:].rstrip()
                    elif comm.startswith("Customer:"):
                        customer = comm[9:].rstrip()
                    else:
                        pass
                    i += 1
                f.close()

                if new_passwd == '':
                    print("ERROR!! Please write unique password in the configuration file!\n Leave script!!!")
                    serialPort.Close()
                    sys.exit()
                elif len(new_passwd) != 10:
                    print("ERROR!! New password s not composed with 10 characters!\n Please correct password in config file\n Leave script!!!")
                    serialPort.Close()
                    sys.exit()
                OnReceiveSerialData()
                print("Set boot loader name")
                serialPort.Send_raw('o')
                backspace = bytearray([8 for i in range(50)])
                OnReceiveSerialData()
                serialPort.serialport.write(backspace)
                time.sleep(1.0)
                OnReceiveSerialData()
                serialPort.Send(bootloader)
                OnReceiveSerialData()
                serialPort.Send('y')
                OnReceiveSerialData()
                print("Set Firmware name")
                serialPort.Send_raw('p')
                OnReceiveSerialData()
                serialPort.serialport.write(backspace)
                time.sleep(1.0)
                OnReceiveSerialData()
                serialPort.Send(firmware)
                OnReceiveSerialData()
                serialPort.Send('y')
                OnReceiveSerialData()
                print("Set TFTP server")
                SetNetwork(IP,TFTP)
                print("Updating bootloader ...")

                fail = True
                serialPort.Send_raw('j')
                while True:
                    time.sleep(3.0)
                    message = serialPort.serialport.read(serialPort.serialport.in_waiting)
                    try:
                        message = message.decode("utf-8", errors='ignore')

                        #print(message)
                        if "PROGRAM SUCCEEDED" in message:
                            fail = False
                            print("Updated bootloader")

                        if "Please press any Enter to continue..." in message:
                            serialPort.Send("")
                            break
                    except:
                        print('decode error')

                if fail:
                    print("Failed to flash bootloader!! Leave script!")
                    serialPort.Close()
                    sys.exit()
                print("Updating Firmware ...")

                fail = True
                serialPort.Send_raw('l')
                while True:
                    time.sleep(2.0)
                    message = serialPort.serialport.read(serialPort.serialport.in_waiting)
                    try:
                        message = message.decode("utf-8", errors='ignore')
                        print('.', end='', flush=True)
                        #print(message)
                        if "FW PROGRAM NORMAL SUCCEEDED" in message:
                            fail = False
                        if "Please press Enter key to continue..." in message:
                            print("Updated firmware")

                            print("")
                            serialPort.Send("")
                            break
                    except:
                        print('decode error')
                if fail:
                    print("Failed to flash firmware!! Leave script!")
                    sys.exit(0)
                time.sleep(1.0)
                #SetNetwork("192.168.100.2", "192.168.100.100")
                #time.sleep(0.5)
                #serialPort.serialport.write(' '.encode("utf-8"))
                print("Set new password")
                serialPort.Send_raw('u')
                OnReceiveSerialData()
                serialPort.Send("@")
                time.sleep(2.0)
                while serialPort.serialport.in_waiting > 0:
                    message =serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8", errors='ignore')
                    print(message)
                    if "=>" in message:
                        break
                    time.sleep(1.0)
                if customer.lower() == "intel":
                    serialPort.Send("sys_eeprom set 0xFD \'0x42 0x36 0x2D 0x30 0x32\'")
                    OnReceiveSerialData()
                set_password = "sys_eeprom set 0x2f " + new_passwd
                serialPort.Send(set_password)
                OnReceiveSerialData()
                time.sleep(0.5)
                serialPort.Send("sys_eeprom")
                OnReceiveSerialData()
                time.sleep(2.0)
                serialPort.Send("sys_eeprom write")
                time.sleep(0.5)
                #serialPort.serialport.write("bootmenu\r".encode("utf-8"))
                #OnReceiveSerialData()
                #message = serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8", errors='ignore')
                message = serialPort.serialport.readline().decode("utf-8", errors='ignore')
                while " Supermicro Switch" not in message:
                    print(message)
                    message =serialPort.serialport.readline().decode("utf-8", errors='ignore')
                login(username, new_passwd)
                new_passwd = ''
                f = open(config_file, 'r')
                commands = f.readlines()
                f.close()
                f = open(config_file, 'w')
                for comm in commands:
                    if comm.startswith("New Password:"):
                        f.write("New Password:\n")
                    else:
                        f.write(comm)
                f.close()
                serialPort.Send("show system information")
                time.sleep(0.5)
                serial_number = ''
                while serialPort.serialport.in_waiting > 0:
                    strs = serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8", errors='ignore')
                    m = re.findall(r"Switch\s+Serial\s+Number\s+\:\s?(\w+)", strs)
                    if m:
                        serial_number = m[0]
                    time.sleep(1.0)
                serialPort.Send_raw('q')
                OnReceiveSerialData()
                serialPort.Send("show version")
                time.sleep(1.0)
                message = ''
                while serialPort.serialport.in_waiting > 0:
                    message += serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8")
                    time.sleep(1.0)
                write_log(serial_number, message)
                print(message + "\nUpdate Finshed!\nTotal time: %s seconds" % (time.time() - start_time))
                #input("Update Finshed! Press enter to continue")
            elif message.endswith("=>"):
                com = input()
                serialPort.Send(com)
                while True:
                    if com == "bootmenu":
                        break
                    while serialPort.serialport.in_waiting:
                        print(serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8", errors='ignore'))
                    com = input()
                    serialPort.Send(com)
else:
    print("Not sent - COM port is closed\r\n")


