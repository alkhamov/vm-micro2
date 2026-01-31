FROM curlimages/curl:8.5.0

WORKDIR /deploy

COPY bpmn ./bpmn
COPY dmn ./dmn
COPY --chmod=755 deploy.sh .

CMD ["./deploy.sh"]

