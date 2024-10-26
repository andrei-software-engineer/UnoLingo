# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# COPY chat_service.py .
COPY requirements.txt . 
# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 6000 for the Flask SocketIO app
EXPOSE 5005

# Set environment variables for Flask
ENV FLASK_APP=chat_service.py



# Run the Flask app with arguments passed to specify the port dynamically
CMD ["python", "chat_service.py", "--port", "5005"]
