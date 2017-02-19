"""
this file contains some useful constants values required for database or the socket server
"""

import os

# check if resources_testing_mode key is found in os.environ which means that
# this is the testing mode so we need to work on a copy of the db
if "resources_testing_mode" in os.environ:
    DATABASE_NAME = "resources_testing.sqlite"
else:
    DATABASE_NAME = "resources.sqlite"

# the host name of the socket server
HOST = ''

# the port number of the socket server
PORT = 8888

# receiving buffer limits
RECV_BUFFER = 1024

# number of seconds required to wait if the required resource is not available, then retry again if failed terminate the connection
TIMEOUT = 10
