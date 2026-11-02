"""유튜브·블로그 최신 글을 모아 feed.json 으로 저장한다.

호스팅에서 하루 한 번 자동 실행하면, 새 영상·글이 올라올 때마다 홈페이지에 저절로 반영된다.
직접 실행: python update_feed.py
"""
import json, re, html, urllib.request, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

CHANNEL_ID = "UC1x_DSHicJ_eYJ0CmsiFw2A"
CHANNEL_HANDLE = "%EC%82%AC%EC%A7%81%EB%A7%88%EB%94%94"  # @사직마디
BLOG_ID = "sajik_madi"
N = 6
UA = {"User-Agent": "Mozilla/5.0"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read().decode("utf-8", "ignore")


def clean_title(t):
    t = re.sub(r"#\S+", "", html.unescape(t))
    return re.sub(r"\s+", " ", t).strip()


def oembed_title(vid):
    d = json.loads(get(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"))
    return d["title"]


def scrape_ids(tab):
    s = get(f"https://www.youtube.com/@{CHANNEL_HANDLE}/{tab}")
    ids = []
    for m in re.finditer(r'"videoId":"([\w-]{11})"', s):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    return ids[:N]


def youtube():
    out = {"videos": []}
    for tab in out:
        try:
            for vid in scrape_ids(tab):
                out[tab].append({"id": vid, "title": clean_title(oembed_title(vid))})
        except Exception as e:
            print("youtube", tab, "실패:", e)
    if not out["videos"]:  # 채널 페이지가 막히면 RSS 로 대신
        try:
            ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
            root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"))
            for e in root.findall("a:entry", ns)[:N]:
                out["videos"].append({"id": e.findtext("yt:videoId", namespaces=ns),
                                      "title": clean_title(e.findtext("a:title", namespaces=ns))})
        except Exception as e:
            print("youtube rss 실패:", e)
    return out


def blog():
    posts = []
    root = ET.fromstring(get(f"https://rss.blog.naver.com/{BLOG_ID}.xml"))
    for it in root.iter("item"):
        if len(posts) >= N:
            break
        link = it.findtext("link").split("?")[0]
        desc = re.sub(r"<[^>]+>", " ", html.unescape(it.findtext("description") or ""))
        desc = re.sub(r"\s+", " ", desc).strip()
        img = ""
        try:
            m = re.search(r'property="og:image" content="([^"]+)"', get(link.replace("blog.naver.com", "m.blog.naver.com")))
            img = m.group(1) if m else ""
        except Exception:
            pass
        posts.append({
            "title": clean_title(it.findtext("title")),
            "link": link,
            "date": parsedate_to_datetime(it.findtext("pubDate")).strftime("%Y.%m.%d"),
            "summary": desc[:90] + ("…" if len(desc) > 90 else ""),
            "image": img,
        })
    return posts


if __name__ == "__main__":
    # 인스타그램은 자동으로 가져올 수 없어(공식 연동 전까지) instagram.txt 에 적어 둔 게시물 주소를 쓴다
    ig = Path(__file__).with_name("instagram.txt")
    links = [l.strip() for l in ig.read_text(encoding="utf-8").splitlines() if l.strip().startswith("http")] if ig.exists() else []
    out = Path(__file__).with_name("feed.json")
    old = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    try:
        posts = blog()
    except Exception as e:
        print("blog 실패:", e)
        posts = []
    data = {**youtube(), "blog": posts, "instagram": links[:N]}
    for k in ("videos", "blog"):  # 가져오기에 실패한 항목은 지난 목록을 그대로 둔다
        if not data[k]:
            data[k] = old.get(k, [])
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print({k: len(v) for k, v in data.items()})
