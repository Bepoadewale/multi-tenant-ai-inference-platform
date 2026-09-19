# ADR 0003: Token-aware limits

Request counts alone do not represent LLM cost/capacity. Estimate prompt plus requested output at admission, constrain tokens/minute and concurrency, then reconcile actual usage.
