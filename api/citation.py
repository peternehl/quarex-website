#!/home/hg6zgvyix7se/virtualenv/public_html/truthangel.org/python/3.11/bin/python3.11_bin
# TruthAngel — citation echo v2: waits 10s, returns items + ask_links

import sys, json, time

DELAY_SECONDS = 3

def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        links = data.get("links") or data.get("urls") or []

        if not isinstance(links, list):
            raise ValueError("`links` must be an array")

        # Simulate work: wait exactly 3 seconds
        time.sleep(DELAY_SECONDS)

        # items: object form (compatible with your earlier consumer)
        items = [{"input": u, "url": u, "status": "ok"} for u in links]

        # ask_links: plain string array copy for ask.api
        ask_links = list(links)

        out = {
            "ok": True,
            "delay_seconds": DELAY_SECONDS,
            "items": items,
            "ask_links": ask_links
        }
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
    except Exception as e:
        sys.stdout.write(json.dumps({"ok": False, "error": str(e)}))

if __name__ == "__main__":
    main()
