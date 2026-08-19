FROM python:3.10-slim
RUN pip install docker psutil requests
WORKDIR /app
COPY autoscaler.py .
CMD ["python", "-u", "autoscaler.py"]
