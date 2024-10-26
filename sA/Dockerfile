# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
COPY auth_service.py .
COPY requirements.txt . 
# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5003 for the Flask app
EXPOSE 5003

# Set environment variables for Flask
ENV FLASK_APP=auth_service.py

# Run the Flask app with arguments passed to specify the port dynamically
# CMD ["python", "auth_service.py", "--port", "5003"]
