FROM selenium/standalone-chrome

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY cogs /cogs
COPY .env .

CMD ["python", "main.py"]
