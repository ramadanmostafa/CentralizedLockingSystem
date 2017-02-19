'''
Simple socket server using threads
'''
import socket
import sys
from thread import *
from lock import Lock
import time
from settings import *

#initiate socket server s
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket created'

#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print 'Socket bind complete'

#Start listening on socket
s.listen(10)
print 'Socket now listening'

#Function for handling connections. This will be used to create threads
def clientthread(conn, client_address):
    #infinite loop so that function do not terminate and thread do not end.
    while True:
        #Receiving from client
        try:
            data = conn.recv(RECV_BUFFER) #release or lock resource_name
        except:
            #release all locked resources for the client address
            client_lock = Lock("", client_address)
            client_lock.release_by_client_address()
            break
        else:
            #split the message Received to get the command and the resource name
            tmp = data.split()

            # check if the message Received follows the correct format
            if tmp is not None and len(tmp) == 2 and ( tmp[0] == "release" or tmp[0] == "lock"):

                # operation has to be lock or release
                operation = tmp[0]
                resource_name = tmp[1]

                #targeted resource name and status
                client_lock = Lock(resource_name, client_address)
                resource_status = client_lock.check_status()

                if not data:
                    break
                elif resource_status is None:
                    # targeted resource is not listed in the database
                    reply = "required resource is not listed"

                elif operation == 'lock' and resource_status == "free":
                    # you gain access to the resource
                    reply = "You have an exclusive access to resource " + resource_name
                    client_lock.acquire()

                elif operation == 'lock' and resource_status == "busy":
                    # the resource is busy, you will wait TIMEOUT secs and retry
                    time.sleep(TIMEOUT)
                    # checking the resource status again after TIMEOUT
                    resource_status_new = client_lock.check_status()

                    if resource_status_new == "busy":
                        # it is still busy, try again later
                        reply = "required resource is busy now, you have to wait a while"
                    else:
                        #it's free now, you will gain access
                        reply = "You have an exclusive access to resource " + resource_name
                        client_lock.acquire()

                elif operation == 'release':
                    if resource_status == "free":
                        #trying to release a free resource, not allowed
                        reply = "resource is already free."

                    #checking if the client who request release is the same client who lock it in the first place
                    elif client_address in client_lock.get_client_address():
                        reply = "lock released from resource " + resource_name
                        client_lock.release()
                    else:
                        # trying to release someone else's resource, not allowed
                        reply = 'it is not allowed to release someone else resource'
            else:
                #the message Received does not follow the correct format so send an error message
                reply = "wrong message, you must send release or lock as the first word then space then the resource_name"

            #send the message to the client
            conn.sendall(reply)

    #came out of loop and close the connection
    conn.close()

#now keep talking with the client
while 1:
    #wait to accept a connection - blocking call
    conn, addr = s.accept()
    client_address = addr[0]
    print 'Connected with ' + client_address + ':' + str(addr[1])

    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    start_new_thread(clientthread ,(conn, client_address))

# close the socket server
s.close()
