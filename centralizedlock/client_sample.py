"""
Simple client that connects to the soket server any lock resourceY then release the lock
"""

import socket
import time

# ip address of the server
HOST = '127.0.0.1'

# port number that the soket server is listening to
PORT = 8888

# initiate the soket client
soket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soket_client.connect((HOST,PORT))

# send a lock request to get access to resourceY
soket_client.sendall('lock resourceY')
data = soket_client.recv(1024)
print 'Received', repr(data)

# sleep for 5 seconds
time.sleep(5)

# release the lock on resourceY
soket_client.sendall('release resourceY')
data = soket_client.recv(1024)
print 'Received', repr(data)

# close the soket client
soket_client.close()
