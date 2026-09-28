import json
from urllib.request import urlopen


def main() -> None:
    try:
        with urlopen("http://localhost:8000/health", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    except Exception as exc:
        print(f"Health check falhou: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
