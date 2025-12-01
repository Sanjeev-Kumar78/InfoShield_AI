FROM python:3.11.14-slim
# Set working directory
WORKDIR /app
# Copy application code
COPY . /app
# Install dependencies
RUN pip install uvicorn && uv sync
# Set environment variables
ENV GOOGLE_API_KEY=GOOGLE_API_KEY
# Expose port
EXPOSE 8000
# Clear the application and restart the server
RUN adk clear && adk migrate
# Start the application
CMD ["adk","web"]