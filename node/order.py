from typing import  Optional
from langchain_core.tools import tool
from database.models import Cars, User, Order
from datetime import datetime
from database.database import session
from langchain_core.tools import tool
from utils import llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser




@tool
def place_order(username: str, car_id: int, car_price: float) -> str:
    """
    Places an order in the database for the given user and car model.

    Args:
        username (str): The username of the user placing the order
        car_id (int): The id of the car model being ordered
        car_price (float): The price of the car model

    Returns:
        str: A success message indicating the order was placed successfully
    """
    # Get the car and user objects from the database
    car = session.query(Cars).filter(Cars.id == car_id).first()
    user = session.query(User).filter(User.username == username).first()

    # Create a new Order object and add it to the database
    new_order = Order(user_id=user.id, car_id=car.id, price=car_price, order_date=datetime.utcnow())
    session.add(new_order)
    session.commit()

    # Return a success message
    return f"Order placed successfully for {car.model} at ${car_price}."




    

