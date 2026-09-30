# API examples

These clients exercise the **existing public inference contract**. They are not a
second gateway, an administrator client, or a source of credentials.

## Run locally

Start the platform first:

```console
make install
make bootstrap-local
make smoke
```

`bootstrap-local` creates short-lived synthetic local tokens in the ignored
`.local/identity/tokens.json` file. Export one only for a local walkthrough:

```console
export INFERENCE_API_TOKEN="$(jq -r '.search' .local/identity/tokens.json)"
```

Then run either example:

```console
./examples/curl-chat.sh
python3.12 examples/python-chat-client.py
```

The default base URL is `http://localhost:8081`; override it with
`INFERENCE_BASE_URL`. Do not commit local tokens or use this synthetic identity
method outside the Compose demonstration.

## Contract boundary

The gateway derives tenant identity from the signed token. A client must not send a
tenant override header. The examples invoke only `/v1/chat/completions`; release,
capacity, usage, and rollout endpoints are administrative surfaces with separately
scoped identities.
