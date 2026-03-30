import os, sys, re, smtplib, ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_TO = os.getenv("EMAIL_TO", "HZ-lu2007@outlook.com")
EMAIL_FROM = os.getenv("EMAIL_FROM", "kimberagent@163.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.163.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "kimberagent@163.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")


def md_to_html(md):
    html = md
    html = re.sub(r"##\s+(.+)", r"<h2>\1</h2>", html)
    html = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"^\*\s(.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"^---$", "", html, flags=re.MULTILINE)
    html = re.sub(r"\n{3,}", "\n\n", html)
    paragraphs = []
    for p in html.split("\n\n"):
        p = p.strip()
        if not p:
            continue
        if p.startswith("<h2>") or p.startswith("<li>") or p.startswith("<strong>") or p.startswith("<em>"):
            paragraphs.append(p)
        else:
            paragraphs.append("<p>" + p + "</p>")
    return "\n".join(paragraphs)


def send_email(filepath):
    if not os.path.exists(filepath):
        print("File not found: " + filepath)
        return False
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if not content.strip():
        print("File is empty")
        return False
    m = re.search(r"(\d{4}-\d{2}-\d{2})", filepath)
    date_str = m.group(1) if m else datetime.now().strftime("%Y-%m-%d")
    body_html = md_to_html(content)
    style = (
        "body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;"
        "line-height:1.7;color:#333;max-width:800px;margin:0 auto;padding:20px;background:#f5f5f5}"
        ".container{background:#fff;padding:30px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}"
        ".header{border-bottom:3px solid #333;padding-bottom:15px;margin-bottom:25px}"
        "h1{color:#333;margin:0;font-size:22px}.date{color:#888;font-size:13px;margin-top:5px}"
        "h2{color:#1a1a1a;border-top:1px solid #e0e0e0;padding-top:20px;margin-top:25px}"
        "a{color:#0066cc}.footer{margin-top:30px;padding-top:15px;border-top:1px solid #e0e0e0;font-size:12px;color:#888;text-align:center}"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        "<style>" + style + "</style></head><body>"
        "<div class=\"container\">"
        "<div class=\"header\"><h1>The New Yorker Daily</h1><div class=\"date\">" + date_str + "</div></div>"
        "<div class=\"content\">" + body_html + "</div>"
        "<div class=\"footer\">Auto-sent by OpenClaw Agent</div>"
        "</div></body></html>"
    )
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "The New Yorker Daily - " + date_str
    msg.attach(MIMEText(html, "html", "utf-8"))
    print("Sending to: " + EMAIL_TO)
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        print("Email sent!")
        return True
    except Exception as e:
        print("Error: " + str(e))
        return False


def main():
    filepath = None
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    if filepath:
        send_email(filepath)
    else:
        print("Usage: python send_email.py <filepath>")


if __name__ == "__main__":
    main()
