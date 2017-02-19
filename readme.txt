Assignment 1
Centralized locking system
-------------------------------------------------------------------------------------
i used socket to implement the server, sqlite3 for the database and pytest for testing.
----------------------------------------------------------------------------------
you need at first to define the resources names in the database.
i already defined resourceX, resourceY and resourceZ for testing purpose

to run it you need to run the socket_server.py first using this command
 python socket_server.py
 then open another terminal and run the client_sample using this command
  python client_sample.py
  or run the test cases implemented using this command
  py.test -q test.py

  you should see 12 passed in 52.24 seconds
