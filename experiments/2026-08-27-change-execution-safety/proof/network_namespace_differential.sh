#!/bin/sh
# The OS-layer half of R2 property (a): the unshared network namespace is
# what denies network, proved by a differential rather than by the flag the
# backend reports about itself.
set -e
PROBE=$(mktemp /tmp/dr-netprobe-XXXXXX.py)
cat > "$PROBE" <<'PY'
import socket
try:
    socket.create_connection(("1.1.1.1", 80), 5).close(); print("CONNECT_OK")
except Exception as e: print("CONNECT_DENIED", type(e).__name__, e)
print("INTERFACES", socket.if_nameindex())
PY
echo "=== INSIDE the backend's own probed prefix (unshare --map-root-user --net) ==="
/usr/bin/unshare --map-root-user --net -- python3 "$PROBE"
echo "=== OUTSIDE (host namespace) ==="
python3 "$PROBE"
rm -f "$PROBE"
