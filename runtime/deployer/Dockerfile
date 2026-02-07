FROM curlimages/curl:8.5.0

WORKDIR /deploy

COPY dmn ./dmn
COPY bpmn ./bpmn
COPY --chmod=755 deploy.sh .

CMD ["./deploy.sh"]
