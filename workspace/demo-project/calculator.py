class Calculator:

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    def percentage(self, value, percent):
        return value * percent / 100

    def average(self, numbers):
        if not numbers:
            raise ValueError("Cannot calculate average of empty list")
        return sum(numbers) / len(numbers)