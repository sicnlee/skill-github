"""
fetch_weather.py

Usage:
    python fetch_weather.py <city>

Fetches current weather for the given city from wttr.in and prints
a formatted Chinese summary following the template in references/OUTPUT_TEMPLATE.md.

Dependencies: Python 3.8+ standard library only (urllib).
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error


def fetch_weather(city: str) -> dict:
    """Fetch raw weather JSON from wttr.in for *city*."""
    encoded_city = urllib.parse.quote(city)
    url = f"https://wttr.in/{encoded_city}?format=j1&lang=zh"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "get-weather-skill/1.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} from wttr.in")
        return json.loads(resp.read().decode("utf-8"))


def parse_current(data: dict) -> dict:
    """Extract the fields needed for the output template."""
    current = data["current_condition"][0]
    return {
        "temp_c": current["temp_C"],
        "weather_desc": current["weatherDesc"][0]["value"],
        "humidity": current["humidity"],
    }


def format_output(city: str, info: dict) -> str:
    """Format the weather info according to references/OUTPUT_TEMPLATE.md."""
    return (
        f"消息来源：源源编写的天气Skills返回\n"
        f"城市：{city}\n"
        f"当前温度：{info['temp_c']}°C\n"
        f"天气状况：{info['weather_desc']}\n"
        f"湿度：{info['humidity']}%"
    )


def main():
    if len(sys.argv) < 2:
        print("用法：python fetch_weather.py <城市名>", file=sys.stderr)
        sys.exit(1)

    city = " ".join(sys.argv[1:])

    try:
        raw = fetch_weather(city)
        info = parse_current(raw)
        print(format_output(city, info))
    except urllib.error.HTTPError as e:
        print(f"错误：无法获取 {city} 的天气信息（HTTP {e.code}），请稍后重试。", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"错误：网络连接失败 — {e.reason}，请检查网络后重试。", file=sys.stderr)
        sys.exit(1)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"错误：返回数据解析失败 — {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
