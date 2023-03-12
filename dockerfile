FROM alpine:3.15
FROM python:3.9

 
WORKDIR /app
COPY ./AppCode  /app/
##COPY C:\Users\user\Downloads\2-foodtrucks\foodtrucks\project\flask-app\* /app/
##RUN npm install
##RUN npm run build

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python","./todo.py" ]
