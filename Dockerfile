# Use lightweight Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy bot files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD ["python", "bot.py"]
