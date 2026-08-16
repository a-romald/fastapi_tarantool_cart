import uuid
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse

from shop.schema import CartSchema, CartCreateSchema, CartUpdateSchema, CartFilterParams, CartSubtractSchema
from shop.cart import Cart, CartItem
from storage.tarantool.storage import TarantulStorage


router = APIRouter()


@router.get("/", response_model=list[CartSchema] | None)
def get_all(filter_query: CartFilterParams = Query()) -> JSONResponse:    
    """ List of all carts with limit and offset """
    try:
        storage = TarantulStorage(space='shop')
        limit = filter_query.limit
        offset = filter_query.offset
        data = storage.list("cart", limit=limit, offset=offset)        
        total_carts = list()
        if data:
            for item in data:
                cart = Cart.from_storable_struct(item)
                cart_dict = cart.to_py_struct()
                total_carts.append(cart_dict)            
            return JSONResponse(total_carts)
        else:
            return JSONResponse(status_code=status.HTTP_200_OK, 
                                content={"message": "No Carts Found"})
    except Exception as e:        
        raise HTTPException(status_code=404, detail=e)


@router.get("/{id}/", response_model=CartSchema | None)
def get(id: uuid.UUID) -> JSONResponse:
    """ Retrieve data of one cart """
    try:
        storage = TarantulStorage(space='shop')
        data = storage.retrieve("cart", id)
        if data:            
            cart = Cart.from_storable_struct(data)
            cart_dict = cart.to_py_struct()
            return JSONResponse(cart_dict)
        else:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, 
                                content={"message": f"Cart with ID {id} does not exist"})
    except Exception as e:        
        raise HTTPException(status_code=404, detail=e)


@router.post("/", response_model=CartSchema | None, status_code=status.HTTP_201_CREATED)
def post(payload: CartCreateSchema) -> JSONResponse:
    """ Create one new cart """
    try:
        storage = TarantulStorage(space='shop')
        cart = Cart()
        cur_uuid = Cart.generate_uuid()        
        items = list()
        cart.id = cur_uuid
        cart.items = list()        
        items = payload.items # Data items from Pydantic model
        cart_items = list()
        for item in items:
            ci = CartItem(sku=item.sku, name=item.name, price=item.price, quantity=item.quantity)
            cart_items.append(ci)
        cart.items = cart_items
        data = cart.to_py_struct()
        storage.create(key_type='cart', key=cur_uuid, data=data)
        # Return new cart
        new_data = storage.retrieve("cart", cur_uuid)
        if new_data:
            new_cart = Cart.from_storable_struct(new_data)
            new_cart_dict = new_cart.to_py_struct()
            return JSONResponse(new_cart_dict)            
        else:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, 
                                content={"message": f"Cart with ID {id} does not exist"})
    except Exception as e:
        raise HTTPException(status_code=422, detail=e)


@router.put("/{id}/", response_model=CartSchema | None)
def update(payload: CartUpdateSchema, id: uuid.UUID) -> JSONResponse:
    """ Update items of one cart """
    try:        
        storage = TarantulStorage(space='shop')
        data = storage.retrieve("cart", id)
        if data:
            cart = Cart.from_storable_struct(data)
            items = payload.items # Data items from Pydantic model
            cart_items = list()
            for item in items:
                ci = CartItem(sku=item.sku, name=item.name, price=item.price, quantity=item.quantity)
                cart_items.append(ci)
            cart.items = cart_items
            cart_dict = cart.to_py_struct()
            storage.update(key_type='cart', key=id, data=cart_dict)
            # Return updated cart
            updated_data = storage.retrieve("cart", id)
            if updated_data:
                upd_cart = Cart.from_storable_struct(updated_data)
                upd_cart_dict =upd_cart.to_py_struct()
                return JSONResponse(upd_cart_dict)            
            else:
                return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, 
                                    content={"message": f"Cart with ID {id} does not exist"})
        else:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, 
                                content={"message": f"Cart with ID {id} does not exist"})
    except Exception as e:        
        raise HTTPException(status_code=404, detail=e)


@router.delete("/{id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete(id: uuid.UUID) -> None:
    """ Delete one cart """
    try:
        storage = TarantulStorage(space='shop')
        data = storage.retrieve("cart", id)
        if data:
            storage.remove("cart", id)
        else:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                                content={"message": f"Cart with ID {id} does not exist"})
    except Exception as e:        
            raise HTTPException(status_code=404, detail=e) 


@router.patch("/add/{id}/", response_model=CartSchema | None)
def add(payload: CartUpdateSchema, id: uuid.UUID) -> JSONResponse:
    """ Add items to one cart """
    try:
        storage = TarantulStorage(space='shop')
        data = storage.retrieve("cart", id)
        if data:
            cart = Cart.from_storable_struct(data)
            cur_cart_items = cart.items # Data items from existing cart
            cur_cart_items_sku = [cur_item.sku for cur_item in cur_cart_items]

            new_items = payload.items # Data items from Pydantic model
            new_cart_items = list()
            for new_item in new_items:
                ci = CartItem(sku=new_item.sku, name=new_item.name, price=new_item.price, quantity=new_item.quantity)
                new_cart_items.append(ci)

            inserted_cart_items = list() # Empty list of items not in current cart            
            for new_cart_item in new_cart_items:
                if new_cart_item.sku in cur_cart_items_sku:
                    for cur_cart_item in cur_cart_items:
                        if cur_cart_item.sku == new_cart_item.sku:
                            if cur_cart_item.price == new_cart_item.price:
                                cur_cart_item.quantity = cur_cart_item.quantity + new_cart_item.quantity
                                for i, ins_item in enumerate(inserted_cart_items):
                                    if ins_item.sku == cur_cart_item.sku and ins_item.price == cur_cart_item.price:
                                        del inserted_cart_items[i]
                                break
                            elif cur_cart_item.price != new_cart_item.price:
                                if new_cart_item not in inserted_cart_items:
                                    inserted_cart_items.append(new_cart_item)
                else:
                    if new_cart_item not in inserted_cart_items:
                        inserted_cart_items.append(new_cart_item)

            total_cart_items = list()
            total_cart_items = cur_cart_items + inserted_cart_items            

            cart.items = list()
            cart.items = total_cart_items
            cart_dict = cart.to_py_struct()
            storage.update(key_type='cart', key=id, data=cart_dict)
            # Return updated cart
            updated_data = storage.retrieve("cart", id)
            if updated_data:
                upd_cart = Cart.from_storable_struct(updated_data)
                upd_cart_dict = upd_cart.to_py_struct()
                return JSONResponse(upd_cart_dict)            
            else:
                return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, 
                                    content={"message": f"Cart with ID {id} does not exist"})
        else:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, 
                                content={"message": f"Cart with ID {id} does not exist"})
    except Exception as e:
        raise HTTPException(status_code=404, detail=e)


@router.patch("/subtract/{id}/", response_model=CartSchema | None)
def subtract(payload: CartSubtractSchema, id: uuid.UUID) -> JSONResponse:
    """ Subtract items from one cart """
    try:
        storage = TarantulStorage(space='shop')
        data = storage.retrieve("cart", id)
        if data:
            cart = Cart.from_storable_struct(data)
            cur_cart_items = cart.items # Data items from existing cart
            cur_cart_items_sku = [cur_item.sku for cur_item in cur_cart_items]
            upd_items = payload.items # Data items from Pydantic model

            for upd_item in upd_items:
                if upd_item.sku in cur_cart_items_sku:
                    for i, cur_cart_item in enumerate(cur_cart_items):
                        if cur_cart_item.sku == upd_item.sku and cur_cart_item.price == upd_item.price:
                            if upd_item.quantity >= cur_cart_item.quantity:
                                del cur_cart_items[i]
                            elif upd_item.quantity < cur_cart_item.quantity:
                                cur_cart_item.quantity = cur_cart_item.quantity - upd_item.quantity

            cart.items = cur_cart_items
            cart_dict = cart.to_py_struct()
            storage.update(key_type='cart', key=id, data=cart_dict)            

            # Return updated cart
            updated_data = storage.retrieve("cart", id)
            if updated_data:
                upd_cart = Cart.from_storable_struct(updated_data)
                upd_cart_dict = upd_cart.to_py_struct()
                return JSONResponse(upd_cart_dict)            
            else:
                return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                                    content={"message": f"Cart with ID {id} does not exist"})
        else:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, 
                                content={"message": f"Cart with ID {id} does not exist"})
    except Exception as e:
            raise HTTPException(status_code=404, detail=e)
