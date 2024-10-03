FROM rapidfort/python-chromedriver:latest-arm64

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y ffmpeg

COPY . .

CMD ["python", "main.py"]
