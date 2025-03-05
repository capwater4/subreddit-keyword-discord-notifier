# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable to prevent Python from writing .pyc files to disc
ENV PYTHONUNBUFFERED=1

# Run the bot script when the container launches
CMD ["python", "skdn.py"]