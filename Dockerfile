# Use the official Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Copy and install dependencies
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Flask will run on
EXPOSE 5003

# Run the Flask app
CMD ["python", "auth_service.py"]
