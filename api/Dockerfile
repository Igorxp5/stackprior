FROM python:3.8.3

COPY . /api/

WORKDIR /api

RUN pip install -r requirements.txt

ENV PYTHONPATH=/

CMD ["python", "__init__.py"]
