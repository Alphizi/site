#!/usr/bin/env python3
"""
Teletype → Clean Beautiful Static HTML Converter (PRO Version)

Этот скрипт делает кардинальный редизайн структуры: 
- Оставляет вашу классическую "теплую" бежевую цветовую палитру.
- Внедряет двухколоночный макет (контент + боковое меню навигации).
- Автоматически генерирует оглавление (Table of Contents) на основе заголовков (h2, h3).
- Значительно улучшает карточки, цитаты и общую читабельность.
- Готов к полностью автоматизированному запуску в GitHub Actions.
"""

import sys
import re
import json
from pathlib import Path

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    print("Нужна библиотека: pip install beautifulsoup4")
    sys.exit(1)


BOOK_CSS = """
:root {
  --bg: #f9f7f2;
  --surface: #ffffff;
  --text: #1f1f1f;
  --text-muted: #5e5952;
  --accent: #2a4a6f;
  --accent-hover: #1e3552;
  --border: #d9d4c8;
  --shadow: rgba(42, 74, 111, 0.06);
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1816;
    --surface: #22201d;
    --text: #e8e4d9;
    --text-muted: #a39a8c;
    --accent: #8aa4c2;
    --accent-hover: #a3b8d1;
    --border: #3a3630;
    --shadow: rgba(0, 0, 0, 0.25);
  }
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.75;
  font-size: 18px;
  margin: 0;
  padding: 0;
  -webkit-font-smoothing: antialiased;
}

/* === Макет === */
.container {
  max-width: 1140px;
  margin: 0 auto;
  padding: 40px 20px 80px;
  display: flex;
  gap: 40px;
  align-items: flex-start;
}

.content {
  flex: 1;
  min-width: 0;
  background: var(--surface);
  padding: 50px 70px;
  border-radius: 16px;
  box-shadow: 0 8px 30px var(--shadow);
  border: 1px solid var(--border);
}

.sidebar {
  width: 300px;
  flex-shrink: 0;
  position: sticky;
  top: 40px;
  max-height: calc(100vh - 80px);
  overflow-y: auto;
}

/* Скрываем скроллбар в сайдбаре для красоты */
.sidebar::-webkit-scrollbar { width: 0px; }

/* === Оглавление (TOC) === */
.toc {
  background: var(--surface);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border);
  box-shadow: 0 4px 20px var(--shadow);
}
.toc h3 {
  margin-top: 0;
  font-size: 0.95rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 10px;
}
.toc ul { list-style: none; padding: 0; margin: 0; }
.toc li { margin-bottom: 10px; }
.toc a {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.95rem;
  display: block;
  transition: color 0.2s, padding-left 0.2s;
  line-height: 1.4;
}
.toc a:hover { 
  color: var(--accent); 
  padding-left: 4px;
}
.toc .toc-h3 { 
  padding-left: 15px; 
  font-size: 0.85rem; 
  margin-top: -4px;
}

/* === Типографика контента === */
h1, h2, h3, h4 { color: var(--text); font-weight: 700; margin-top: 0; }
h1 { 
  font-size: 2.6rem; 
  line-height: 1.15; 
  margin-bottom: 1.2em; 
  letter-spacing: -0.02em;
}
h2 { 
  font-size: 1.8rem; 
  margin: 1.8em 0 0.8em; 
  border-bottom: 2px solid var(--border); 
  padding-bottom: 0.3em; 
}
h3 { font-size: 1.4rem; margin: 1.5em 0 0.6em; }
p { margin: 0 0 1.2em; }
a { 
  color: var(--accent); 
  text-decoration: none; 
  font-weight: 500; 
  border-bottom: 1px solid transparent; 
  transition: all 0.2s; 
}
a:hover { 
  border-bottom-color: var(--accent); 
  color: var(--accent-hover); 
}

/* === Цитаты (Blockquote) === */
blockquote {
  margin: 2em 0;
  padding: 1.5em 2em 1.5em 3.5em;
  background: var(--bg);
  border-left: 4px solid var(--accent);
  border-radius: 0 12px 12px 0;
  font-style: italic;
  color: var(--text-muted);
  position: relative;
}
blockquote::before {
  content: "“";
  font-size: 5em;
  position: absolute;
  top: -15px;
  left: 10px;
  color: var(--border);
  font-family: Georgia, serif;
  line-height: 1;
}
blockquote p { position: relative; z-index: 1; margin-bottom: 0; }
blockquote p + p { margin-top: 1em; }

/* === Медиа и Изображения === */
figure { margin: 2.5em 0; text-align: center; }
figure img { 
  max-width: 100%; 
  height: auto; 
  border-radius: 8px; 
  box-shadow: 0 4px 16px var(--shadow); 
}
figcaption { margin-top: 0.8em; font-size: 0.9em; color: var(--text-muted); }

.video-container {
  position: relative;
  padding-bottom: 56.25%;
  height: 0;
  margin: 1.5em 0;
  background: #000;
  border-radius: 12px;
  box-shadow: 0 4px 20px var(--shadow);
  overflow: hidden;
}
.video-container iframe {
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
  border: 0;
}

/* === Блоки внимания (Callouts) === */
.callout {
  margin: 2em 0;
  padding: 1.5em 1.8em;
  border-radius: 12px;
  border-left: 5px solid var(--accent);
  background: var(--bg);
  box-shadow: 0 2px 12px var(--shadow);
}
.callout p:last-child { margin-bottom: 0; }
.callout-blue   { border-left-color: #4a6fa5; background: #e8eef7; }
.callout-amber  { border-left-color: #b38b4d; background: #f5f0e6; }
.callout-purple { border-left-color: #9b6b8a; background: #f7eef4; }
.callout-green  { border-left-color: #4a8a6f; background: #e8f3ed; }
.callout-neutral { border-left-color: #6b6257; background: #f0e9dc; }

@media (prefers-color-scheme: dark) {
  .callout-blue   { background: #1e2a3a; border-left-color: #7aa0d1; }
  .callout-amber  { background: #2f2a1f; border-left-color: #d4b37a; }
  .callout-purple { background: #2a2430; border-left-color: #c48fb3; }
  .callout-green  { background: #1f2a24; border-left-color: #7ab89a; }
  .callout-neutral { background: #2c2a26; border-left-color: #a89f90; }
}

hr {
  border: none;
  height: 2px;
  background: var(--border);
  margin: 3em 0;
}

/* === Адаптивность (Мобильные) === */
@media (max-width: 992px) {
  .container { flex-direction: column-reverse; padding: 20px 16px; }
  .sidebar { width: 100%; position: static; margin-top: 20px; }
  .content { padding: 40px 24px; }
  h1 { font-size: 2.2rem; }
}
"""


def extract_content(soup: BeautifulSoup) -> BeautifulSoup:
    main = None
    for sel in [
        'article[itemprop="articleBody"]',
        'article.article__content',
        '.article-body',
        '.post-content',
    ]:
        node = soup.select_one(sel)
        if node and len(node.get_text(strip=True)) > 150:
            main = node
            break

    if main is None:
        script = soup.find("script", string=re.compile(r"window\.__INITIAL_STATE__"))
        if script:
            m = re.search(r"window\.__INITIAL_STATE__=(\{.*?\});", script.string or "", re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                    articles = data.get("articles", {}).get("items", {})
                    best = max((a.get("text", "") for a in articles.values()), key=len, default="")
                    if len(best) > 150:
                        main = BeautifulSoup(best, "html.parser")
                except Exception:
                    pass

    if main is None:
        main = soup.find("article") or soup.find("body") or soup

    result = BeautifulSoup(str(main), "html.parser")

    # Переносим секции (как было в старом скрипте)
    existing_anchors = {
        s.get("anchor") or s.get("data-anchor")
        for s in result.find_all("section")
        if s.get("anchor") or s.get("data-anchor")
    }

    for section in soup.find_all("section"):
        has_bg = "bg=" in str(section) or "background-color" in str(section.get("style", ""))
        if not has_bg:
            continue

        anchor = section.get("anchor") or section.get("data-anchor")
        if anchor and anchor in existing_anchors:
            continue

        cloned = BeautifulSoup(str(section), "html.parser").find("section")
        if cloned:
            result.append(cloned)
            if anchor:
                existing_anchors.add(anchor)

    return result


def update_links(soup: BeautifulSoup):
    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "teletype.media" in href:
            m = re.search(r"teletype\.media/[@\w.]+/([^/?#]+)", href)
            if m:
                slug = m.group(1)
                a["href"] = f"{slug}.html"
                continue

        if re.match(r"^/?@[\w.]+/", href):
            m = re.search(r"@[\w.]+/([^/?#]+)", href)
            if m:
                slug = m.group(1)
                a["href"] = f"{slug}.html"
                continue

        # Превращаем ссылки без расширения в локальные .html (кроме внешних и якорей)
        if (not href.startswith(("http://", "https://", "#", "mailto:", "tel:")) 
            and "." not in href.split("/")[-1]
            and not href.endswith(".html")):
            a["href"] = href.rstrip("/") + ".html"
            
        # Заменяем Main.html на index.html для главной страницы
        if "Main.html" in a["href"]:
            a["href"] = a["href"].replace("Main.html", "index.html")


def clean_and_convert(soup: BeautifulSoup) -> BeautifulSoup:
    body = soup.body or soup

    # Спасаем картинки
    for noscript in body.find_all("noscript"):
        img = noscript.find("img")
        if img:
            noscript.replace_with(img)
        else:
            noscript.decompose()

    # Чистим скрипты и стили
    for tag in body.find_all(["script", "style"]):
        tag.decompose()

    # Очистка Teletype document/image тегов
    for doc in body.find_all("document"):
        doc.unwrap()
        
    for custom_img in body.find_all("image"):
        figure = soup.new_tag("figure")
        new_img = soup.new_tag("img")
        if custom_img.get("src"):
            new_img["src"] = custom_img["src"]
        figure.append(new_img)
        
        caption = custom_img.find("caption")
        if caption and caption.get_text(strip=True):
            figcaption = soup.new_tag("figcaption")
            for child in list(caption.contents):
                figcaption.append(child)
            figure.append(figcaption)
            
        custom_img.replace_with(figure)

    for c in body.find_all(string=re.compile(r"^\s*<!--\s*\[?--\]?")):
        c.extract()

    # Цветные блоки -> Callouts
    def get_callout_type(color: str) -> str:
        if not color: return "neutral"
        m = re.search(r'hsl\(?\s*([0-9.]+)', color)
        if not m: return "neutral"
        try: hue = float(m.group(1))
        except: return "neutral"
        if 200 <= hue <= 260: return "blue"
        if 40 <= hue <= 70: return "amber"
        if 300 <= hue <= 340: return "purple"
        if 140 <= hue <= 180: return "green"
        return "neutral"

    for sec in body.find_all("section"):
        style = sec.get("style", "") or ""
        bg = sec.get("bg", "")
        color = ""
        if "background-color" in style:
            m = re.search(r"background-color:\s*([^;]+)", style)
            if m: color = m.group(1).strip()
        elif bg:
            color = bg.strip()

        callout_type = get_callout_type(color)
        callout = soup.new_tag("div", attrs={"class": f"callout callout-{callout_type}"})

        for child in list(sec.children):
            callout.append(child)
        sec.replace_with(callout)

    update_links(body)

    for callout in body.find_all("div", class_="callout"):
        for a in callout.find_all("a", attrs={"name": True}):
            a.decompose()
        for c in callout.find_all(string=lambda s: isinstance(s, str) and "<!--" in s):
            c.extract()

    # Очистка мусорных атрибутов
    for tag in body.find_all(True):
        for attr in list(tag.attrs):
            if attr.startswith(("data-", "data-v-", "on", "name")) and attr != "name":
                del tag[attr]
        if tag.name == "a" and tag.get("target") == "_blank":
            del tag["target"]

    for img in body.find_all("img", src=True):
        img["src"] = img["src"].split("/")[-1].split("?")[0]
        for bad in ("width", "height", "style", "itemprop"):
            if bad in img.attrs:
                del img[bad]
        
        if not img.find_parent("figure"):
            figure = soup.new_tag("figure")
            img.wrap(figure)

    # Видео с ютуба
    for yt in body.find_all("youtube"):
        src = yt.get("src", "")
        vid = None
        if "youtu.be/" in src:
            vid = src.split("youtu.be/")[-1].split("?")[0]
        elif "watch?v=" in src:
            vid = src.split("watch?v=")[-1].split("&")[0]
        if vid:
            div = soup.new_tag("div", attrs={"class": "video-container"})
            ifr = soup.new_tag("iframe", attrs={
                "src": f"https://www.youtube.com/embed/{vid}",
                "allowfullscreen": "",
                "frameborder": "0"
            })
            div.append(ifr)
            yt.replace_with(div)

    for ifr in body.find_all("iframe"):
        src = ifr.get("src", "")
        if src.endswith(".html") and not src.startswith("http"):
            m = re.search(r"([A-Za-z0-9_-]{8,})\.html", src)
            if m:
                ifr["src"] = f"https://www.youtube.com/embed/{m.group(1)}"
        if not ifr.find_parent("div", class_="video-container"):
            div = soup.new_tag("div", attrs={"class": "video-container"})
            ifr.wrap(div)

    # Чистим пустые SVG
    for svg in body.find_all("svg"):
        classes = svg.get("class", []) or []
        if isinstance(classes, str): classes = classes.split()
        vb = svg.get("viewBox", "") or svg.get("viewbox", "")
        if "spacer" in classes or ("0 0 16 9" in vb and len(list(svg.children)) == 0):
            svg.decompose()

    # Удаляем пустые теги
    for _ in range(2):
        for tag in body.find_all(["p", "div", "span"]):
            if tag.find_parent("div", class_="callout"):
                continue
            if not tag.get_text(strip=True) and not tag.find(["img", "iframe", "video", "h1", "h2", "h3", "figure"]):
                tag.decompose()

    for wrap in body.find_all("div", class_="wrap"):
        wrap.unwrap()

    return soup


def generate_toc(soup: BeautifulSoup):
    """Генерирует оглавление на основе тегов h2 и h3."""
    toc_html = ""
    headers = soup.find_all(['h2', 'h3'])
    
    if len(headers) > 1: # Показываем TOC только если больше 1 заголовка
        toc_html += "<ul>\n"
        for i, header in enumerate(headers):
            text = header.get_text(strip=True)
            if not text: continue
            
            # Создаем валидный ID для навигации
            anchor_id = f"section-{i}"
            header['id'] = anchor_id
            
            level_class = f"toc-{header.name}" # toc-h2 или toc-h3
            toc_html += f'  <li class="{level_class}"><a href="#{anchor_id}">{text}</a></li>\n'
            
        toc_html += "</ul>"
        
    return toc_html


def build_html(title: str, content: BeautifulSoup) -> str:
    # Генерация оглавления и расстановка ID
    toc_content = generate_toc(content)
    
    sidebar_html = ""
    if toc_content:
        sidebar_html = f"""
        <aside class="sidebar">
          <nav class="toc">
            <h3>Содержание</h3>
            {toc_content}
          </nav>
        </aside>
        """

    body_html = str(content.body or content)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
{BOOK_CSS.strip()}
  </style>
</head>
<body>
  <div class="container">
    {sidebar_html}
    <main class="content">
      <article>
        <h1>{title}</h1>
        {body_html}
      </article>
    </main>
  </div>
</body>
</html>"""


def convert_file(input_path: Path, output_path: Path):
    print(f"Обрабатываю: {input_path.name}")
    raw = input_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "html.parser")

    title = "Без названия"
    if t := soup.find("title"):
        title = t.get_text(strip=True).replace(" — Teletype", "").strip()
    for h in soup.find_all(["h1", "h2", "h3"]):
        t = h.get_text(strip=True)
        if 3 < len(t) < 140 and not t.lower().startswith("пост "):
            title = t
            break

    content = extract_content(soup)
    if not content or len(content.get_text(strip=True)) < 100:
        print("  Не удалось извлечь содержимое")
        return False

    content = clean_and_convert(content)
    html = build_html(title, content)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"  Готово: {output_path.name}")
    return True


def main():
    if len(sys.argv) < 3:
        print("Использование: python converter_pro.py <папка_источник> <папка_результат>")
        sys.exit(1)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    if not src.exists() or not src.is_dir():
        print(f"Ошибка: Исходная папка '{src}' не найдена.")
        sys.exit(1)

    dst.mkdir(parents=True, exist_ok=True)
    html_files = sorted(src.glob("*.html"))
    print(f"Найдено файлов для конвертации: {len(html_files)}")

    for f in html_files:
        convert_file(f, dst / f.name)

    print("Все файлы успешно конвертированы!")

if __name__ == "__main__":
    main()
