"""
DESCRIPTION
===========

The module is used to work with temporary data storage.

This data has a limited shelf life but should not be deleted due to memory shortage.

The module operates on key/value data:

* A key consists of two parts: the type and the key itself.
* A type is a namespace for separate storage of various entities (sessions, carts, etc.)
* Keys are unique within a type.
* The data stores a structure.
* The key lifetime is specified in seconds from the current time; the expiration time is recorded in Unix time.

USING
========

from store.tarantul.starage import TarantulStorage

storage = TarantulStorage(host='localhost', space='shop')

cart = storage.get("cart", "dfe3052b-e8bc-4c8b-9f45-d51d2c8c412c")
"""

import os
from time import time
import tarantool
from tarantool.const import (
    RECONNECT_MAX_ATTEMPTS,
    RECONNECT_DELAY,
)

from config import settings

"""
The default key storage time in TarantulStorage is 24 hours
settings.DEFAULT_TARANTOOL_TTL = 86400
"""

PRIMARY_INDEX = 'primary'
TYPE_INDEX = 'type'
LIMIT_ONCE = 1
LIMIT_TOTAL = 10
OFFSET_START = 0

host = os.getenv("TARANTOOL_HOST", "localhost")
port = int(os.getenv("TARANTOOL_PORT", 3301))


class TarantulStorage:    
    """ Access to persistent data storage """

    def __init__(self, host=host, port=port, user=None, password=None, space=None, connect_timeout=1, request_timeout=5):
        """ Constructor of an object containing a connection to the storage

        Args:

        * host (str): Storage address. Domain name or IP.

        * port (int): Storage port. Optional.
        Default value - 3301 (the standard Tarantool port).

        * space (str): Name of the table where the data is stored. String.
        Tables (spaces in Tarantool terminology) and their properties are specified in the storage configuration.        

        * connect_timeout (int): Connection timeout. Seconds.
        Default value is 1.

        * request_timeout (int): Request timeout. Seconds.
        Default value is 1.

        Returns:

        * (None): None

        """
        self.host = host
        self.port = int(port)
        self.space = space
        self.request_timeout = request_timeout
        self.client = tarantool.Connection(host=self.host, port=self.port,
                                           user=user,
                                           password=password,
                                           connection_timeout=int(connect_timeout),
                                           socket_timeout=int(request_timeout),
                                           reconnect_max_attempts=RECONNECT_MAX_ATTEMPTS,
                                           reconnect_delay=RECONNECT_DELAY,
                                           connect_now=True,
                                           encoding=None)


    def list(self, key_type, limit=None, offset=None):
                """ Read data from storage.
                    If successful, the method returns the data in the same format as it was previously 
                    passed to the <create> method (or returned by the data constructor).
        
                    The data is always returned in Unicode (wide). If the data was serialized,
                    it must be converted to bytes before deserialization.
        
                    If an error occurs, the method throws an exception.
        
                Args:
        
                * key_type (str): An arbitrary name for the data type. For example, 'session', 'cart', 'page', etc.
        
                Returns:
        
                * The method returns list of data or None if nothing was found in the key.
        
                """
                if not offset:
                     offset = OFFSET_START

                if not limit:
                     limit = LIMIT_TOTAL
                
                rows = self.client.select(
                    space_name=self.space,
                    index=TYPE_INDEX,
                    limit=limit,
                    offset=offset,
                    key=key_type,
                )
        
                if len(rows) == 0:
                    return None
                
                rows_list = list()
                if rows:
                    for row in rows:
                        rows_list.append(row[2])

                return rows_list


    def retrieve(self, key_type, key):
            """ Read data from storage.
                If successful, the method returns the data in the same format as it was previously 
                passed to the <create> method (or returned by the data constructor).
    
                The data is always returned in Unicode (wide). If the data was serialized,
                it must be converted to bytes before deserialization.
    
                If an error occurs, the method throws an exception.
    
            Args:
    
            * key_type (str): An arbitrary name for the data type. For example, 'session', 'cart', 'page', etc.
    
            * key (str): Any arbitrary (but unique within the type) key name. For example, '1234', 'key1/25', etc.
    
            Returns:
    
            * The method returns data or None if nothing was found in the key.
    
            """       
    
            tkey = [str(key_type), str(key)]        
            
            rows = self.client.select(
                space_name=self.space,
                index=PRIMARY_INDEX,
                limit=LIMIT_ONCE,
                offset=OFFSET_START,
                key=tkey,
            )        
    
            if len(rows) == 0:
                return None
    
            return rows[0][2]


    def create(self, key_type, key, data, ttl=settings.DEFAULT_TARANTOOL_TTL):
            """ Write data to storage
    
            Args:
    
            * key_type (str): Temporary data type.
            Any data type name. For example, 'session', 'cart', 'page', etc.
    
            * key (str): Any arbitrary (but unique within the type) key name. For example, '1234', 'key1/25', etc.
    
            * data (any): Data. Structures (dictionary, tuple, or list), strings, bytes, and numbers are allowed.
            If the data is an object or if the structure contains references
            to objects, such data must first be serialized (for example, via Storable).
    
            * ttl (Optional(int)): Data lifetime in storage. The lifetime is specified in seconds.
            In storage, the lifetime will be added to the current time
            and recorded as an expiration time (unix time), after which the data will be deleted.
    
            The default is one day.
    
            Returns:
    
            * (list): If successful, the method returns a reference to an array corresponding to the data and metadata written 
            to the storage. If an error occurs, the method throws an exception.
            ```
                      [
                          key_type, # Type
                          key,      # Key
                          data,     # Data
                          expires,  # Expiration time (time of recording + ttl)
                      ]
            ```
            """
            expires = int(time()) + ttl
            payload = [
                str(key_type),
                str(key),
                data,
                expires,
            ]        
            self.client.insert(self.space, payload)
    
            return payload


    def update(self, key_type, key, data, ttl=settings.DEFAULT_TARANTOOL_TTL):
        """ Write data to storage

        Args:

        * key_type (str): Temporary data type.
        Any data type name. For example, 'session', 'cart', 'page', etc.

        * key (str): Any arbitrary (but unique within the type) key name. For example, '1234', 'key1/25', etc.

        * data (any): Data. Structures (dictionary, tuple, or list), strings, bytes, and numbers are allowed.
        If the data is an object or if the structure contains references
        to objects, such data must first be serialized (for example, via Storable).

        * ttl (Optional(int)): Data lifetime in storage. The lifetime is specified in seconds.
        In storage, the lifetime will be added to the current time
        and recorded as an expiration time (unix time), after which the data will be deleted.

        The default is one day.

        Returns:

        * (list): If successful, the method returns a reference to an array corresponding to the data and metadata written 
        to the storage. If an error occurs, the method throws an exception.
        ```
                  [
                      key_type, # Type
                      key,      # Key
                      data,     # Data
                      expires,  # Expiration time (time of recording + ttl)
                  ]
        ```
        """
        expires = int(time()) + ttl
        payload = [
            str(key_type),
            str(key),
            data,
            expires,
        ]        
        self.client.replace(self.space, payload)

        return payload


    def remove(self, key_type, key):
        """ Delete data from storage.
            If successful, the method returns the string '0 but true'.
            If an error occurs, the method throws an exception.

        Args:

        * key_type (str): Any arbitrary name for the data type. For example, 'session', 'cart', 'page', etc.

        * key (str): Any arbitrary (but unique within the type) key name. For example, '1234', 'key1/25', etc.

        Returns:

        * (str): The method returns the string '0 but true'.

        """       

        tkey = [str(key_type), str(key)]

        self.client.delete(self.space, tkey)

        return '0 but true'
