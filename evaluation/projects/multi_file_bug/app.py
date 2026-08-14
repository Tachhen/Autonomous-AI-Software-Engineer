from greeting import greet
from user import User


def welcome(name):
    user = User(name)
    return greet(user).upper()
