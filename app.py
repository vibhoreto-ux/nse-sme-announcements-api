import requests
import time
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

NSE_BASE_URL = "https://www.nseindia.com"
ANNOUNCEMENTS_API = NSE_BASE_URL + "/api/corporate-announcements?segment=SME"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": NSE_BASE_URL + "/companies-listing/corporate-filings-announcements",
    "Connection": "keep-alive",
    "Origin": NSE_BASE_URL
}


def fetch_sme_announcements(session, max_retries=3):
    session.get(NSE_BASE_URL, headers=HEADERS)
    retries = 0
    while retries < max_retries:
        try:
            response = session.get(ANNOUNCEMENTS_API, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "data" in data:
                return data["data"]
            else:
                app.logger.warning("API response missing 'data' key")
                return []
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Request error: {e}, retrying ({retries}/{max_retries})")
            retries += 1
            time.sleep(2 * retries)
    return []


def parse_sme_announcement_item(item):
    return {
        "announcementId": item.get("id") or "",
        "symbol": item.get("symbol") or "",
        "companyName": item.get("companyName") or "",
        "subject": item.get("subject") or "",
        "announcementTime": item.get("announcementTime") or "",
        "formattedTime": format_time(item.get("announcementTime")),
        "pdfUrl": item.get("attachmentUrl") or "",
        "segment": "SME",
        "documentType": item.get("documentType") or "",
        "description": item.get("description") or ""
    }


def format_time(timestr):
    try:
        dt = datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
        return dt.isoformat()
    except Exception:
        return timestr


@app.route("/api/sme_announcements", methods=["GET"])
def sme_announcements():
    with requests.Session() as session:
        announcements = fetch_sme_announcements(session)
        parsed = [parse_sme_announcement_item(a) for a in announcements]
        if not parsed:
            return jsonify({"status": "error", "message": "Failed to fetch or no SME announcements found."}), 500
        return jsonify({
            "status": "success",
            "count": len(parsed),
            "data": parsed
        })


if __name__ == "__main__":
    app.run(debug=True, port=8080)
