# 1. Base Image
FROM python:3.14-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy files from your local current directory to the container's WORKDIR
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# Start the FastAPI app
CMD [ "python", "main.py" ]
