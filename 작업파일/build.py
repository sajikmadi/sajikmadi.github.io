"""src.html + 이미지 + feed.json → ../올릴파일/index.html (사진을 파일 안에 넣어 한 파일로 만든다)"""
import base64, io, json, shutil
from pathlib import Path
from PIL import Image

here = Path(__file__).parent
def b64(path, fmt, size, **kw):
    im = Image.open(path)
    if fmt == "WEBP" and im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGB")
    im.thumbnail(size)
    b = io.BytesIO(); im.save(b, fmt, **kw)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()

s = (here / "src.html").read_text(encoding="utf-8")
s = s.replace("{{DOC}}", b64(here / "img/doctor.png", "WEBP", (700, 1050), quality=88))
s = s.replace("{{LOGO}}", b64(here / "img/logo.png", "PNG", (420, 80), optimize=True))
s = s.replace("{{MAP}}", b64(here / "img/map.jpg", "WEBP", (1100, 1100), quality=82))
for i in range(1, 8):
    s = s.replace(f"{{{{WHO{i}}}}}", b64(here / f"img/who{i}.png", "WEBP", (160, 160), quality=85))
s = s.replace("{{SYMIMG}}", b64(here / "img/symptoms.png", "WEBP", (1300, 1500), quality=82))
s = s.replace("{{FEED}}", (here / "feed.json").read_text(encoding="utf-8"))
out = here.parent / "올릴파일"
out.mkdir(exist_ok=True)
(out / "index.html").write_text(s, encoding="utf-8")
shutil.copy(here / "feed.json", out / "feed.json")
for f in (here / "media").iterdir():  # 첫 화면 배경 영상처럼 따로 두는 파일
    shutil.copy(f, out / f.name)
print("올릴파일/index.html", len(s) // 1024, "KB")
