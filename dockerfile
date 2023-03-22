FROM python:3.9

WORKDIR /app
COPY ./AppCode/requirements.txt  /app/
RUN pip install --no-cache-dir -r requirements.txt
 

COPY ./AppCode  /app/
CMD [ "python","./todo.py" ]
