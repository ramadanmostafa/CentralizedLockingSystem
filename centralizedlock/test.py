"""
this file contains some test cases that connects to the soket server as a client
and also check the database.
"""

import socket
import time
import os
from shutil import copyfile
from lock import Lock
from database_functions import *

# put the resources_testing_mode key in os.environ which means that
# this is the testing mode so we need to work on a copy of the db
os.environ['resources_testing_mode'] = "1"

# ip address of the server
HOST = '127.0.0.1'

# port number that the soket server is listening to
PORT = 8888

def setup():
    """
    make a copy of the database
    """
    copyfile('resources.sqlite', 'resources_testing.sqlite')

def test_lock_resourceX_then_unlock():
    """
    TestCase Senario:
    the client try to lock the resourceX then release the
    lock on the resourceX
    """
    #targeted resource and client_address
    resource_name = 'resourceX'
    resource_id = get_resource_id_by_name(resource_name)[0]
    client_address = '127.0.0.1'
    client_lock = Lock(resource_name, client_address)
    status = client_lock.check_status()

    #initiate socket s and send the request access to resourceX
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST,PORT))
    if status == 'free':
        s.sendall('lock resourceX')
        data = s.recv(1024)

        # make sure the access is granted
        assert data == 'You have an exclusive access to resource resourceX'
        assert client_lock.check_status() == 'busy'

        # make sure this operation stored into the db
        #select operations
        # client_ip_address, operation_time, operation_type
        operations = get_operations_by_resource_id(resource_id)
        assert len(operations) == 1
        assert operations[0][0] == client_address
        assert operations[0][2] == "lock"

        # sleep for 5 seconds
        time.sleep(5)

        # release the lock on resourceX
        s.sendall('release resourceX')
        data = s.recv(1024)

        # make sure the release done
        assert data == 'lock released from resource resourceX'
        assert client_lock.check_status() == 'free'

        # make sure this operation stored into the db
        #select operations
        # client_ip_address, operation_time, operation_type
        operations = get_operations_by_resource_id(resource_id)
        assert len(operations) == 2
        assert operations[0][0] == client_address
        assert operations[0][2] == "lock"
        assert operations[1][0] == client_address
        assert operations[1][2] == "release"

    elif status == 'busy':
        s.sendall('lock resourceX')
        data = s.recv(1024)
        assert data == 'required resource is busy now, you have to wait a while'
        assert client_lock.check_status() == 'busy'

    #delete operations
    delete_operation_by_resource_id(resource_id)

    #close the socket client
    s.close()

def test_release_locked_resource_by_different_client():
    """
    TestCase Senario:
    at first lock the resourceX by the client 192.168.0.1
    then ask the server as the client 127.0.0.1 to lock or release the resourceX
    """
    #targeted resource and client_address
    resource_name = 'resourceX'
    client_address1 = '127.0.0.1'
    client_address2 = '192.168.0.1'
    client_lock = Lock(resource_name, client_address1)
    status = client_lock.check_status()

    #initiate socket s and send the request access to resourceX
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST,PORT))
    if status == 'free':
        # lock the resourceX by the client '192.168.0.1'
        update_resource_status(resource_name, 'busy', client_address2)

    #make sure the resourceX status is busy
    assert client_lock.check_status() == 'busy'
    s.sendall('lock resourceX')
    data = s.recv(1024)

    #make sure the resourceX status is busy
    assert data == 'required resource is busy now, you have to wait a while'
    assert client_lock.check_status() == 'busy'
    s.sendall('release resourceX')
    data = s.recv(1024)

    #make sure the resourceX status is busy and the release failed because the ip is different
    assert data == 'it is not allowed to release someone else resource'
    assert client_lock.check_status() == 'busy'
    update_resource_status(resource_name, 'free', client_address2)

    #make sure the resourceX status is free
    assert client_lock.check_status() == 'free'

    #close the socket client
    s.close()

def test_lock_resourceX_then_close_connection():
    """
    TestCase Senario:
    the client try to lock the resourceX then this client close the connection.
    when the connection between the client and the server is down, the server should release the
    lock on the resourceX automatically
    """
    #targeted resource and client_address
    resource_name = 'resourceX'
    resource_id = get_resource_id_by_name(resource_name)[0]
    client_address = '127.0.0.1'
    client_lock = Lock(resource_name, client_address)
    status = client_lock.check_status()

    #initiate socket s and send the request access to resourceX
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST,PORT))
    if status == 'free':
        s.sendall('lock resourceX')
        data = s.recv(1024)

        # make sure the access is granted
        assert data == 'You have an exclusive access to resource resourceX'
        assert client_lock.check_status() == 'busy'

        # make sure this operation stored into the db
        #select operations
        # client_ip_address, operation_time, operation_type
        operations = get_operations_by_resource_id(resource_id)
        assert len(operations) == 1
        assert operations[0][0] == client_address
        assert operations[0][2] == "lock"

        # the client terminate the connection
        s.close()

        #delete operations
        delete_operation_by_resource_id(resource_id)
    elif status == 'busy':
        s.sendall('lock resourceX')
        data = s.recv(1024)

        # make sure the resourceX is busy
        assert data == 'required resource is busy now, you have to wait a while'
        assert client_lock.check_status() == 'busy'

        # the client terminate the connection
        s.close()

    # sleep for 5 seconds to make sure the server cleaning up is done
    time.sleep(5)

    # make sure the server make resourceX free after the client terminates the connection
    assert client_lock.check_status() == 'free'

def test_access_locked_resource():
    """
    TestCase Senario:
    the first client s1 lock resourceX for a while.
    the second client s2 try to access resourceX which is locked by s1 so the request refused
    then s1 release the lock and set resourceX free
    """
    #targeted resource and client_address
    resource_name = 'resourceX'
    resource_id = get_resource_id_by_name(resource_name)[0]
    client_address = '127.0.0.1'
    client_lock = Lock(resource_name, client_address)
    status = client_lock.check_status()

    #initiate socket s1 and send the request access to resourceX
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s1.connect((HOST,PORT))
    if status == 'free':
        s1.sendall('lock resourceX')
        data = s1.recv(1024)

        # make sure the access is granted
        assert data == 'You have an exclusive access to resource resourceX'
        assert client_lock.check_status() == 'busy'

        # make sure this operation stored into the db
        #select operations
        # client_ip_address, operation_time, operation_type
        operations = get_operations_by_resource_id(resource_id)
        assert len(operations) == 1
        assert operations[0][0] == client_address
        assert operations[0][2] == "lock"

    #initiate socket s2 and send the request access to resourceX
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.connect((HOST,PORT))
    s2.sendall('lock resourceX')
    data = s2.recv(1024)

    # make sure the resourceX is busy and access is not granted
    assert data == 'required resource is busy now, you have to wait a while'
    assert client_lock.check_status() == 'busy'

    # the client terminate the connection
    s2.close()

    # s1 release the lock on resourceX
    s1.sendall('release resourceX')
    data = s1.recv(1024)

    # make sure the lock released and status is free now
    assert data == 'lock released from resource resourceX'
    assert client_lock.check_status() == 'free'

    # make sure this operation stored into the db
    #select operations
    # client_ip_address, operation_time, operation_type
    operations = get_operations_by_resource_id(resource_id)
    assert len(operations) == 2
    assert operations[0][0] == client_address
    assert operations[0][2] == "lock"
    assert operations[1][0] == client_address
    assert operations[1][2] == "release"

    #delete operations
    delete_operation_by_resource_id(resource_id)

    # the client terminate the connection
    s1.close()

def test_access_locked_resource_then_unlock_before_timeout():
    """
    TestCase Senario:
    there are 2 sockets s1 and s2. s1 lock resourceX then s2 tries to access resourceX but he couldn't so s2 have to wait TIMEOUT
    to retry but before the TIMEOUT ends, s1 release the lock so resourceX become free when TIMEOUT ends and s2 retries to access
    resourceX then it gains exclusive access to resourceX.
    """
    #targeted resource and client_address
    resource_name = 'resourceX'
    resource_id = get_resource_id_by_name(resource_name)[0]
    client_address = '127.0.0.1'
    client_lock = Lock(resource_name, client_address)
    status = client_lock.check_status()

    #initiate socket s1 and lock resourceX
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s1.connect((HOST,PORT))
    if status == 'free':
        s1.sendall('lock resourceX')
        data = s1.recv(1024)

        #make sure the access is granted and resourceX is busy
        assert data == 'You have an exclusive access to resource resourceX'
        assert client_lock.check_status() == 'busy'

        # make sure this operation stored in the database
        #select operations
        # client_ip_address, operation_time, operation_type
        operations = get_operations_by_resource_id(resource_id)
        assert len(operations) == 1
        assert operations[0][0] == client_address
        assert operations[0][2] == "lock"

    # initiate socket s2 and try to lock resourceX but fails
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.connect((HOST,PORT))
    s2.sendall('lock resourceX')
    assert client_lock.check_status() == 'busy'

    # before TIMEOUT ends, s1 release resourceX
    s1.sendall('release resourceX')
    data = s1.recv(1024)

    # make sure it released the resource successfully and resourceX is free
    assert data == 'lock released from resource resourceX'
    assert client_lock.check_status() == 'free'

    # make sure this operation stored in the database
    #select operations
    # client_ip_address, operation_time, operation_type
    operations = get_operations_by_resource_id(resource_id)
    assert len(operations) == 2
    assert operations[0][0] == client_address
    assert operations[0][2] == "lock"
    assert operations[1][0] == client_address
    assert operations[1][2] == "release"

    # close socket connection
    s1.close()

    # when s2 retries again, it locks resourceX and have an exclusive access
    data = s2.recv(1024)

    #make sure the access is granted and resourceX is busy
    assert data == 'You have an exclusive access to resource resourceX'
    assert client_lock.check_status() == 'busy'

    # make sure this operation stored in the database
    #select operations
    # client_ip_address, operation_time, operation_type
    operations = get_operations_by_resource_id(resource_id)
    assert len(operations) == 3
    assert operations[0][0] == client_address
    assert operations[0][2] == "lock"
    assert operations[1][0] == client_address
    assert operations[1][2] == "release"
    assert operations[2][0] == client_address
    assert operations[2][2] == "lock"

    # s2 release resourceX
    s2.sendall('release resourceX')
    data = s2.recv(1024)

    # make sure it released the resource successfully and resourceX is free
    assert data == 'lock released from resource resourceX'
    assert client_lock.check_status() == 'free'

    # make sure this operation stored in the database
    #select operations
    # client_ip_address, operation_time, operation_type
    operations = get_operations_by_resource_id(resource_id)
    assert len(operations) == 4
    assert operations[0][0] == client_address
    assert operations[0][2] == "lock"
    assert operations[1][0] == client_address
    assert operations[1][2] == "release"
    assert operations[2][0] == client_address
    assert operations[2][2] == "lock"
    assert operations[3][0] == client_address
    assert operations[3][2] == "release"

    #delete operations
    delete_operation_by_resource_id(resource_id)
    
    # close socket connection
    s2.close()

def test_operations():
    """
    TestCase Senario:
    the main purpose of this test case is to make sure that the insertion into operations table
    works good by trying to lock resourceZ then check the database
    then release the lock on resourceZ then check the database again
    """
    #targeted resource and client_address
    resource_name = 'resourceZ'
    resource_id = get_resource_id_by_name(resource_name)[0]

    #get number of operations stored in the database for the resourceZ
    initial_operations_length = len(get_operations_by_resource_id(resource_id))
    client_address = '127.0.0.1'
    client_lock = Lock(resource_name, client_address)
    status = client_lock.check_status()

    #initiate socket s and send the request access to resourceZ
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST,PORT))
    if status == 'free':
        s.sendall('lock resourceZ')
        data = s.recv(1024)

        #make sure resourceZ is busy and you gain access
        assert data == 'You have an exclusive access to resource resourceZ'
        assert client_lock.check_status() == 'busy'

        # make sure this operation stored into the db
        #select operations
        # client_ip_address, operation_time, operation_type
        operations = get_operations_by_resource_id(resource_id)
        assert len(operations) == 1 + initial_operations_length
        assert operations[initial_operations_length][0] == client_address
        assert operations[initial_operations_length][2] == "lock"

        # sleep for 2 secs
        time.sleep(2)
        s.sendall('release resourceZ')
        data = s.recv(1024)

        # make sure the lock released and the resourceZ is free now
        assert data == 'lock released from resource resourceZ'
        assert client_lock.check_status() == 'free'

        # make sure this operation stored into the db
        #select operations
        # client_ip_address, operation_time, operation_type
        operations = get_operations_by_resource_id(resource_id)
        assert len(operations) == 2 + initial_operations_length
        assert operations[initial_operations_length][0] == client_address
        assert operations[initial_operations_length][2] == "lock"
        assert operations[1 + initial_operations_length][0] == client_address
        assert operations[1 + initial_operations_length][2] == "release"

    elif status == 'busy':
        s.sendall('lock resourceZ')
        data = s.recv(1024)
        assert data == 'required resource is busy now, you have to wait a while'
        assert client_lock.check_status() == 'busy'

    #close the socket client
    s.close()

def test_lock_resource_then_die():
    """
    TestCase Senario:
    the client try to lock the resourceX then this client die.
    when the connection between the client and the server is down, the server should release the
    lock on the resourceX automatically
    """
    #targeted resource and client_address
    resource_name = 'resourceX'
    resource_id = get_resource_id_by_name(resource_name)[0]
    client_address = '127.0.0.1'
    client_lock = Lock(resource_name, client_address)
    status = client_lock.check_status()

    #initiate socket s and send the request access to resourceX
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST,PORT))
    if status == 'free':
        s.sendall('lock resourceX')
        data = s.recv(1024)

        # make sure the access is granted
        assert data == 'You have an exclusive access to resource resourceX'
        assert client_lock.check_status() == 'busy'

        # make sure this operation stored into the db
        #select operations
        # client_ip_address, operation_time, operation_type
        operations = get_operations_by_resource_id(resource_id)
        assert len(operations) == 1
        assert operations[0][0] == client_address
        assert operations[0][2] == "lock"

    #delete operations
    delete_operation_by_resource_id(resource_id)

    # the client terminate the connection
    s.close()

    # sleep for 5 seconds to make sure the server cleaning up is done
    time.sleep(5)

    # make sure the server make resourceX free after the client die
    assert client_lock.check_status() == 'free'

def test_release_free_resource():
    """
    TestCase Senario:
    trying to send a release request for a free resource which is not allowed
    so the wrong message response is expected.
    """
    #targeted resource and client_address
    resource_name = 'resourceX'
    client_address = '127.0.0.1'
    client_lock = Lock(resource_name, client_address)
    status = client_lock.check_status()

    #initiate socket s and send the release request for resourceX
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST,PORT))
    s.sendall('release resourceX')
    data = s.recv(1024)

    #expecting error message as a response
    assert data == 'resource is already free.'

    # the status of the resource was free and still free
    assert client_lock.check_status() == 'free'

    #close the socket client
    s.close()

def test_worng_message():
    """
    TestCase Senario:
    trying to send a message to the server that not follow the format <lock or release> <resource name> which is not allowed
    so the wrong message response is expected.
    """
    #initiate socket s and send the message to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST,PORT))
    s.sendall('Hi Socket')
    data = s.recv(1024)

    #expecting error message as a response
    assert data == 'wrong message, you must send release or lock as the first word then space then the resource_name'

    #close the socket client
    s.close()

def test_send_empty_message():
    """
    TestCase Senario:
    trying to send an empty message to the server which is not allowed
    so the wrong message response is expected.
    """
    #initiate socket s and send an empty message to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST,PORT))
    s.sendall(' ')
    data = s.recv(1024)

    #expecting error message as a response
    assert data == 'wrong message, you must send release or lock as the first word then space then the resource_name'

    #close the socket client
    s.close()

def test_access_unlisted_resource():
    """
    TestCase Senario:
    trying to acquire access to an unlisted resource which is not allowed
    so the wrong message response is expected.
    """
    #initiate socket s and lock UnknownResource
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST,PORT))
    s.sendall('lock UnknownResource')
    data = s.recv(1024)

    #expecting error message as a response
    assert data == 'required resource is not listed'

    #close the socket client
    s.close()

def test_lock_multiple_resources():
    """
    TestCase Senario:
    trying to acquire access to more that one resource in a single time which is not allowed
    so the wrong message response is expected.
    """
    #initiate socket s and lock resourceX and resourceY
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST,PORT))
    s.sendall('lock resourceX resourceY')
    data = s.recv(1024)

    #expecting error message as a response
    assert data == 'wrong message, you must send release or lock as the first word then space then the resource_name'

    #close the socket client
    s.close()
