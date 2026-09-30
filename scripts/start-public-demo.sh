#!/usr/bin/env bash
set -euo pipefail

# Start the real local flagship demonstration, then create a temporary public
# Cloudflare Quick Tunnel for the operator console. This is intentionally not a named
# tunnel, does not write credentials, and does not change Cloudflare account state.

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

if ! command -v cloudflared >/dev/null 2>&1; then
  command -v brew >/dev/null 2>&1 || {
    echo 'cloudflared is required. Install Homebrew or install cloudflared manually.' >&2
    exit 1
  }
  echo 'Installing cloudflared with Homebrew…'
  brew install cloudflared
fi

make install
make bootstrap-local
make smoke
make demo-flagship

tunnel_log=$(mktemp -t multi-tenant-ai-platform-tunnel.XXXXXX)
tunnel_pid=''
cleanup() {
  if [[ -n "$tunnel_pid" ]] && kill -0 "$tunnel_pid" 2>/dev/null; then
    kill "$tunnel_pid" 2>/dev/null || true
  fi
  rm -f "$tunnel_log"
}
trap cleanup EXIT INT TERM

echo 'Creating a temporary public Cloudflare Quick Tunnel…'
cloudflared tunnel --url http://localhost:8091 --protocol http2 >"$tunnel_log" 2>&1 &
tunnel_pid=$!

public_url=''
for _ in $(seq 1 30); do
  public_url=$(sed -nE 's#.*(https://[^[:space:]]+\.trycloudflare\.com).*#\1#p' "$tunnel_log" | head -n 1 || true)
  if [[ -n "$public_url" ]]; then
    break
  fi
  if ! kill -0 "$tunnel_pid" 2>/dev/null; then
    cat "$tunnel_log" >&2
    echo 'Cloudflare Quick Tunnel exited before a public URL was created.' >&2
    exit 1
  fi
  sleep 1
done

if [[ -z "$public_url" ]]; then
  cat "$tunnel_log" >&2
  echo 'Timed out waiting for a Cloudflare Quick Tunnel URL.' >&2
  exit 1
fi

echo
echo 'Public flagship operator console:'
echo "${public_url}/#/scenario"
echo
echo 'This URL is temporary and public. Keep it for controlled demonstrations only.'
echo 'Press Ctrl-C to stop the tunnel. The local Docker stack remains running.'

if [[ "${PUBLIC_DEMO_EXIT_AFTER_URL:-0}" == '1' ]]; then
  exit 0
fi
wait "$tunnel_pid"
