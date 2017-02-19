"""
this file contains functions that connects to the database and update it.
"""
import sqlite3
from settings import DATABASE_NAME

def connect():
    """
    connect to the sqlite database and return the connection

    :rtype: sqlite db connection
    """
    con = sqlite3.connect(DATABASE_NAME)
    return con

def get_resource_status(resource_name):
    """
    get resource status by resource name and return a tuple of a value free or busy

    :param str resource_name: a unique identifier for a resource

    :rtype: None
    """
    conn = connect()
    cur = conn.cursor()
    sql_query = "select resources_names.current_state from resources_names where resources_names.resource_name = ?"
    cur.execute(sql_query, (resource_name,))
    data = cur.fetchone()
    conn.close()
    return data

def update_resource_status(resource_name, resource_status, client_address):
    """
    update the status and client address of a resource. can be used in acquire or release lock

    :param str resource_name: a unique identifier for a resource
    :param str resource_status: the status of a specific resource, free or busy
    :param str client_address: the ip address of the client

    :rtype: None
    """
    conn = connect()
    cur = conn.cursor()
    sql_query = "update resources_names set current_state = ?, client_address = ? where resources_names.resource_name = ?"
    cur.execute(sql_query,(resource_status, client_address, resource_name))
    conn.commit()
    conn.close()

def release_resource_by_client_address(client_address):
    """
    given a client address then make this resource status is free,
    used to free the resource after the client disconnected.

    :param str client_address: the ip address of the client

    :rtype: None
    """
    conn = connect()
    cur = conn.cursor()
    sql_query = "update resources_names set current_state = ?, client_address = null where client_address = ?"
    cur.execute(sql_query,("free", client_address))
    conn.commit()
    conn.close()

def get_client_address_by_resourceName(resource_name):
    """
    get the client address of a given resource name

    :param str resource_name: a unique identifier for a resource

    :rtype: tuple
    """
    conn = connect()
    cur = conn.cursor()
    sql_query = "select resources_names.client_address from resources_names where resources_names.resource_name = ?"
    cur.execute(sql_query, (resource_name,))
    data = cur.fetchone()
    conn.close()
    return data

def get_resource_id_by_name(resource_name):
    """
    get the resource id of a given resource name

    :param str resource_name: a unique identifier for a resource

    :rtype: tuple
    """
    conn = connect()
    cur = conn.cursor()
    sql_query = "select resources_names.resource_id from resources_names where resources_names.resource_name = ?"
    cur.execute(sql_query, (resource_name,))
    data = cur.fetchone()
    conn.close()
    return data

def insert_operation(resource_id, operation_time, operation_type, client_address):
    """
    insert a row data into operations table.

    :param str resource_id: a unique identifier for a resource
    :param str operation_time: time that this operation happened
    :param str operation_type: the type of an operation, lock or release
    :param str client_address: the ip address of the client

    :rtype: None
    """
    conn = connect()
    cur = conn.cursor()
    sql_query = "insert into operations(client_ip_address, operation_time, operation_type, resource_id) values(?, ?, ?, ?)"
    cur.execute(sql_query,(client_address, operation_time, operation_type, resource_id))
    conn.commit()
    conn.close()

def delete_operation_by_resource_id(resource_id):
    """
    delete all the rows with specific resource_id.

    :param str resource_id: a unique identifier for a resource

    :rtype: None
    """
    conn = connect()
    cur = conn.cursor()
    sql_query = "delete from operations where operations.resource_id = ?"
    cur.execute(sql_query, (resource_id,))
    conn.commit()
    conn.close()

def get_resource_ids_by_client_address(client_address):
    """
    get all resources ids for a specific client ip address

    :param str client_address: the ip address of the client

    :rtype: 2 d tuple
    """
    conn = connect()
    cur = conn.cursor()
    sql_query = "select resources_names.resource_id from resources_names where resources_names.client_address = ?"
    cur.execute(sql_query, (client_address,))
    data = cur.fetchall()
    conn.close()
    return data

def get_operations_by_resource_id(resource_id):
    """
    select operations information that related to specific resource.

    :param str resource_id: a unique identifier for a resource

    :rtype: 2 d tuple, (client_ip_address, operation_time, operation_type)
    """
    conn = connect()
    cur = conn.cursor()
    sql_query = "select client_ip_address, operation_time, operation_type from operations where resource_id = ?"
    cur.execute(sql_query, (resource_id,))
    data = cur.fetchall()
    conn.close()
    return data
