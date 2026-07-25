import os
import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}

def get_proxies():
    proxy_url = os.getenv('PROXY_URL') or os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
    if proxy_url:
        return {'http': proxy_url, 'https': proxy_url}
    return None

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def clean_title(title_text):
    t = clean_text(title_text)
    t = re.sub(r'\s*새글$', '', t)
    return t

def parse_date(date_str):
    date_str = clean_text(date_str)
    m = re.search(r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', date_str)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m_short = re.search(r'(\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})', date_str)
    if m_short:
        year = "20" + m_short.group(1)
        return f"{year}-{int(m_short.group(2)):02d}-{int(m_short.group(3)):02d}"
    return date_str

def fetch_mnd():
    url = "https://www.mnd.go.kr/mnd/156/subview.do"
    posts = []
    proxies = get_proxies()
    try:
        resp = requests.get(url, headers=HEADERS, proxies=proxies, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        table = soup.find('table')
        if not table:
            print("[MND] Table not found")
            return posts

        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else table.find_all('tr')
        
        for row in rows:
            tds = row.find_all(['td', 'th'])
            if not tds or len(tds) < 4:
                continue
            
            a_tag = row.find('a')
            if not a_tag:
                continue
            
            title = clean_title(a_tag.get_text())
            if not title:
                continue
                
            href = a_tag.get('href', '')
            if href.startswith('/'):
                link = f"https://www.mnd.go.kr{href}"
            elif not href.startswith('http'):
                link = f"https://www.mnd.go.kr/mnd/156/{href}"
            else:
                link = href
                
            col_texts = [clean_text(td.get_text()) for td in tds]
            num = col_texts[0] if col_texts else ""
            
            date = ""
            for text in reversed(col_texts):
                parsed = parse_date(text)
                if re.match(r'^\d{4}-\d{2}-\d{2}$', parsed):
                    date = parsed
                    break
            
            author = col_texts[2] if len(col_texts) > 2 else ""
            views = col_texts[-1] if len(col_texts) > 4 and col_texts[-1].isdigit() else "0"
            
            post_id = f"mnd-{num}" if num.isdigit() else f"mnd-{abs(hash(link))}"
            
            posts.append({
                "id": post_id,
                "category": "국방부",
                "category_code": "mnd",
                "num": num,
                "title": title,
                "author": author,
                "date": date,
                "views": views,
                "link": link
            })
        print(f"[MND] Successfully scraped {len(posts)} posts")
    except Exception as e:
        print(f"[MND] Error fetching posts: {e}")
    return posts

def fetch_army():
    url = "https://www.army.mil.kr/army/24/subview.do"
    posts = []
    proxies = get_proxies()
    try:
        resp = requests.get(url, headers=HEADERS, proxies=proxies, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        table = soup.find('table')
        if not table:
            print("[ARMY] Table not found")
            return posts

        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else table.find_all('tr')
        
        for row in rows:
            tds = row.find_all(['td', 'th'])
            if not tds or len(tds) < 4:
                continue
            
            a_tag = row.find('a')
            if not a_tag:
                continue
            
            title = clean_title(a_tag.get_text())
            if not title:
                continue
                
            href = a_tag.get('href', '')
            if href.startswith('/'):
                link = f"https://www.army.mil.kr{href}"
            elif not href.startswith('http'):
                link = f"https://www.army.mil.kr/army/24/{href}"
            else:
                link = href
                
            col_texts = [clean_text(td.get_text()) for td in tds]
            num = col_texts[0] if col_texts else ""
            
            date = ""
            for text in reversed(col_texts):
                parsed = parse_date(text)
                if re.match(r'^\d{4}-\d{2}-\d{2}$', parsed):
                    date = parsed
                    break

            author = col_texts[3] if len(col_texts) > 3 else (col_texts[1] if len(col_texts) > 1 else "")
            views = ""
            for text in col_texts:
                if text.isdigit() and text != num:
                    views = text
                    
            post_id = f"army-{num}" if num.isdigit() else f"army-{abs(hash(link))}"
            
            posts.append({
                "id": post_id,
                "category": "육군",
                "category_code": "army",
                "num": num,
                "title": title,
                "author": author,
                "date": date,
                "views": views,
                "link": link
            })
        print(f"[ARMY] Successfully scraped {len(posts)} posts")
    except Exception as e:
        print(f"[ARMY] Error fetching posts: {e}")
    return posts

def main():
    print("Starting scraping process...")
    mnd_posts = fetch_mnd()
    army_posts = fetch_army()
    
    all_posts = mnd_posts + army_posts
    all_posts.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(all_posts),
        "mnd_count": len(mnd_posts),
        "army_count": len(army_posts),
        "posts": all_posts
    }
    
    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "posts.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved {len(all_posts)} posts to {output_path}")

if __name__ == "__main__":
    main()
