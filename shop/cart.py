from typing import List
from typing import List
from datetime import datetime, timedelta, timezone
import uuid

from config import settings


current_timezone = timezone(timedelta(hours=settings.CURRENT_UTC), name=settings.TIMEZONE_NAME)


class CartItem:
    """ Cart component """
    def __init__(self, sku=None, name=None, quantity=None, price=None):
        """ Constructor
        Args:        
        * sku (int): Product code (Stock Keeping Unit)
        * name (int): Product name
        * quantity (int): Number of items in the cart
        * price (float): Float unit price
        Returns:
        * (CardItem): Cart item.
        """        
        self.sku = sku
        self.name = name
        self.quantity = quantity
        self.price = price

    @classmethod
    def from_storable_struct(cls, data: dict):
        """ Method recreates an object from Tarantool data structure
        Args:
        * cls (type): Class
        * data (dict): Structure with data
        Returns:
        * (CardItem): Cart component
        """        
        newdata = dict()
        for key, value in data.items():            
            newkey = key.decode("UTF-8")
            newval = value.decode("UTF-8") if isinstance(value, bytes) else value
            newdata[newkey] = newval
        instance = cls()        
        instance.sku = newdata['sku']
        instance.name = newdata['name']
        instance.quantity = newdata['quantity']
        instance.price = newdata['price']        
        return instance

    @classmethod
    def from_py_struct(cls, data: dict):
        """ Method recreates an object from python data structure
        Args:
        * cls (type): Class
        * data (dict): Structure with data
        Returns:
        * (CardItem): Cart component
        """
        instance = cls()        
        instance.sku = data['sku']
        instance.name = data['name']
        instance.quantity = data['quantity']
        instance.price = data['price']        
        return instance

    def to_py_struct(self):
        """Method returns a structure with object's data
        Returns:
        * (dict): Structure with data of cart component.
        """
        return {            
            'sku': self.sku,
            'name': self.name,
            'quantity': self.quantity,
            'price': self.price,
        }


class Cart:
    """Shopping Cart"""
    id: str
    items: List[CartItem]
    created: datetime.datetime

    def __init__(self, id=None, items:list[CartItem] = []):
        """ Constructor
        Args:
        * id (int): Cart UUID
        * items (list(CartItem)): List of cart components
        Returns:
        * (Cart): Cart.
        """
        self.id = id
        self.items = items
        self.created = datetime.now()

    @classmethod
    def from_storable_struct(cls, data: dict):        
        newdata = dict()
        for key, value in data.items():            
            newkey = key.decode("UTF-8")
            newval = value.decode("UTF-8") if isinstance(value, bytes) else value
            newdata[newkey] = newval
        """ The method recreates an object from a data structure.
        Args:
        * cls (type): Class
        * data (dict): Structure with data
        Returns:
        * (Cart): Cart
        """        
        instance = cls()
        instance.id = newdata.get('id')
        items = list()
        for item in newdata.get('items', []):
            items.append(CartItem.from_storable_struct(item))
        instance.items = items
        instance.created = datetime.fromisoformat(newdata.get('created'))
        return instance

    def to_py_struct(self):
        """ The method returns a structure with the object's data
        Returns:
        * (dict): Structure with cart data
        """        
        return {
            'id': self.id,
            'items': [item.to_py_struct() for item in self.items],            
            'created': str(self.created.replace(tzinfo=current_timezone).isoformat()), # 2026-07-25T14:37:15.240667+03:00
        }

    @classmethod
    def from_py_struct(cls, data: dict):
        """ The method recreates an object from a data structure
        Args:
        * cls (type): Class
        * data (dict): Structure with data
        Returns:
        * (Cart): Cart
        """
        instance = cls()
        instance.id = data.get('id')
        items = list()
        for item in data.get('items', []):            
            items.append(CartItem.from_py_struct(item))
        instance.items = items
        instance.created = data.get('created')
        return instance

    @classmethod
    def generate_uuid(cls):
        """ The method generates uuid
        Args:
        * cls (type): Class
        Returns:
        * (string): uuid.UUID
        """
        # Generate a random UUID (Version 4)
        return str(uuid.uuid4())
