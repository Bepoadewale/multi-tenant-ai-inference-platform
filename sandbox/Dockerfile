FROM python:3.12-alpine
RUN apk add --no-cache git \
    && addgroup -S sandbox \
    && adduser -S -G sandbox -u 65532 sandbox
COPY sandbox/fixture-repo /opt/fixture-repo
RUN git -C /opt/fixture-repo init \
    && git -C /opt/fixture-repo config user.name fixture \
    && git -C /opt/fixture-repo config user.email fixture@local.invalid \
    && git -C /opt/fixture-repo add . \
    && git -C /opt/fixture-repo commit -m fixture \
    && chown -R 65532:65532 /opt/fixture-repo
LABEL com.bepoadewale.project=multi-tenant-ai-inference-platform \
      inference.platform.resource=sandbox-image
USER 65532:65532
WORKDIR /workspace
