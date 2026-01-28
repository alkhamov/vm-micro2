FROM curlimages/curl:8.5.0

WORKDIR /deploy

COPY bpmn ./bpmn
COPY dmn ./dmn
COPY deploy.sh .

RUN chmod +x deploy.sh

CMD ["./deploy.sh"]
