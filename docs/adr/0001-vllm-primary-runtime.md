# ADR 0001: vLLM is the primary GPU runtime

vLLM provides an OpenAI-compatible server and continuous-batching-oriented serving model. The gateway keeps an adapter boundary so alternatives can be evaluated without moving tenant controls into runtimes.
