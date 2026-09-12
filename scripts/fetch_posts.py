import os
import json
import re
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
from bs4 import BeautifulSoup

def load_env_file(filepath=".env"):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception as e:
            print(f"[Warning] Failed to load .env: {e}")

load_env_file()

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

def request_with_retry(url, headers=HEADERS, proxies=None, max_retries=3, timeout=15):
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
            resp.encoding = 'utf-8'
            if resp.status_code == 200:
                return resp
            print(f"[Retry {attempt}/{max_retries}] HTTP {resp.status_code} for {url}")
        except Exception as e:
            print(f"[Retry {attempt}/{max_retries}] Request failed for {url}: {e}")
        if attempt < max_retries:
            time.sleep(2 * attempt)
    return None

def send_email_notification(new_posts):
    if not new_posts:
        return
        
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    mail_to = os.getenv("MAIL_TO", "jfchae1483@gmail.com")
    
    if not gmail_user or not gmail_password:
        print("[Email] GMAIL_USER 또는 GMAIL_APP_PASSWORD가 설정되지 않아 메일을 발송하지 않습니다.")
        return

    subject = f"[국방부/육군 채용봇] 신규 공고 {len(new_posts)}건이 등록되었습니다."
    
    items_html = ""
    for post in new_posts:
        category = post.get("category", "공고")
        title = post.get("title", "")
        author = post.get("author", "")
        date = post.get("date", "")
        link = post.get("link", "#")
        badge_bg = "#2563eb" if category == "국방부" else "#16a34a"
        
        items_html += f"""
        <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; background: #ffffff;">
            <div style="display: inline-block; padding: 3px 8px; background-color: {badge_bg}; color: #ffffff; border-radius: 4px; font-size: 12px; font-weight: bold; margin-bottom: 8px;">
                {category}
            </div>
            <h3 style="margin: 0 0 8px 0; font-size: 15px; color: #1e293b; line-height: 1.4;">
                <a href="{link}" target="_blank" style="color: #1e293b; text-decoration: none;">
                    {title}
                </a>
            </h3>
            <div style="font-size: 12px; color: #64748b; margin-bottom: 12px;">
                <span>담당: {author}</span> | <span>등록일: {date}</span>
            </div>
            <a href="{link}" target="_blank" style="display: inline-block; padding: 6px 12px; background-color: #0f172a; color: #ffffff; text-decoration: none; border-radius: 4px; font-size: 12px; font-weight: 500;">
                공고 원문 보기 &rarr;
            </a>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; padding: 20px; color: #334155; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;">
            <div style="background: #0f172a; padding: 20px; color: white;">
                <h2 style="margin: 0; font-size: 18px;">🛡️ 국방부 & 육군 신규 채용공고 알림</h2>
                <p style="margin: 6px 0 0 0; font-size: 13px; opacity: 0.85;">새롭게 등록된 공고 {len(new_posts)}건이 감지되었습니다.</p>
            </div>
            <div style="padding: 20px; background: #f8fafc;">
                {items_html}
            </div>
            <div style="padding: 14px 20px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                본 메일은 국방부/육군 채용공고 모니터링 시스템에서 자동 발송되었습니다.
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"국방부 채용알림봇 <{gmail_user}>"
    msg["To"] = mail_to
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, [mail_to], msg.as_string())
        print(f"[Email] 알림 메일 발송 완료 -> {mail_to} (신규 공고 {len(new_posts)}건)")
    except Exception as e:
        print(f"[Email] 메일 발송 실패: {e}")


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
        resp = request_with_retry(url, headers=HEADERS, proxies=proxies, timeout=15)
        if not resp:
            print("[MND] Error fetching posts: request returned no response after retries")
            return posts
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
        resp = request_with_retry(url, headers=HEADERS, proxies=proxies, timeout=15)
        if not resp:
            print("[ARMY] Error fetching posts: request returned no response after retries")
            return posts
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
    
    output_path = os.path.join("data", "posts.json")
    
    # 기존 데이터 로드 (전체/부분 실패 시 기존 데이터 보존 및 fallback, 신규 공고 감지용)
    existing_posts = []
    existing_ids = set()
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_posts = existing_data.get("posts", [])
                existing_ids = {p.get("id") or p.get("link") for p in existing_posts}
        except Exception as e:
            print(f"[Warning] Failed to read existing {output_path}: {e}")

    # 부분 실패 방어: 한 기관만 실패했을 경우 기존 데이터에서 유지
    if not mnd_posts and existing_posts:
        mnd_existing = [p for p in existing_posts if p.get("category_code") == "mnd"]
        if mnd_existing:
            print(f"[Fallback] 국방부 수집 실패: 기존 국방부 데이터({len(mnd_existing)}건)를 유지합니다.")
            mnd_posts = mnd_existing

    if not army_posts and existing_posts:
        army_existing = [p for p in existing_posts if p.get("category_code") == "army"]
        if army_existing:
            print(f"[Fallback] 육군 수집 실패: 기존 육군 데이터({len(army_existing)}건)를 유지합니다.")
            army_posts = army_existing

    all_posts = mnd_posts + army_posts
    
    # 수집 결과가 0건일 경우 기존 파일을 덮어쓰지 않고 보호
    if not all_posts:
        print("[WARNING] 수집된 게시글이 0건(total_count: 0)입니다. 기존 데이터를 보호하기 위해 data/posts.json을 덮어쓰지 않습니다.")
        return

    # 신규 등록 공고 감지 (기존 데이터가 있었던 경우에만 비교)
    new_posts = []
    if existing_ids:
        new_posts = [p for p in all_posts if (p.get("id") or p.get("link")) not in existing_ids]

    if new_posts:
        print(f"[Notification] {len(new_posts)}건의 신규 공고가 감지되었습니다. 이메일 알림을 발송합니다.")
        send_email_notification(new_posts)
    else:
        print("[Notification] 새로운 공고가 없습니다. (이메일 발송 생략)")

    all_posts.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(all_posts),
        "mnd_count": len(mnd_posts),
        "army_count": len(army_posts),
        "posts": all_posts
    }
    
    os.makedirs("data", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved {len(all_posts)} posts to {output_path}")

if __name__ == "__main__":
    main()

