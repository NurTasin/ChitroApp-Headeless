FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
EXPOSE 5000
ENV OPENAI_API_KEY="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"
ENV CHITRO_LOGIN_CODE="05021977"
CMD ["python3", "app.py"]
