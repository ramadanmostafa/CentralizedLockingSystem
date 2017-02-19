"""
this file contains the implementation of the Lock class which is responsible for
interacting with the database
"""
from database_functions import *
from datetime import datetime

class Lock(object):
    """
    this class is responsible for lock or release resources
    """
    def __init__(self, resource_name, client_address):
        """
        the constructor of the class Lock

        :param str resource_name: a unique identifier for a resource
        """
        self.resource_name = resource_name
        self.client_address = client_address

    def check_status(self):
        """
        get the status of a resource. free or busy

        :rtype: str
        """
        status = get_resource_status(self.resource_name)
        if status is not None:
            return status[0]
        else:
            return None

    def acquire(self):
        """
        lock the selected resource

        :rtype: None
        """
        update_resource_status(self.resource_name, "busy", self.client_address)
        #insert row
        resource_id = get_resource_id_by_name(self.resource_name)[0]
        insert_operation(resource_id, str(datetime.now()), "lock", self.client_address)

    def release(self):
        """
        release the selected resource

        :rtype: None
        """
        update_resource_status(self.resource_name, "free", self.client_address)
        #insert row
        resource_id = get_resource_id_by_name(self.resource_name)[0]
        insert_operation(resource_id, str(datetime.now()), "release", self.client_address)

    def release_by_client_address(self):
        """
        release the selected resources related to the selected client ip address

        :rtype: None
        """
        release_resource_by_client_address(self.client_address)
        #insert rows
        resource_ids = get_resource_ids_by_client_address(self.client_address)
        for resource_id in resource_ids:
            insert_operation(resource_id[0], str(datetime.now()), "release", self.client_address)

    def get_client_address(self):
        """
        get the client ip address that has locked the selected resource

        :rtype: tuple
        """
        return get_client_address_by_resourceName(self.resource_name)
