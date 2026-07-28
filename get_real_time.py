import asyncio
import os
import re
from playwright.async_api import async_playwright
import gspread

# --- CẤU HÌNH ---
GOOGLE_SHEET_NAME = "https://docs.google.com/spreadsheets/d/1rCGTw4GdGlR4K-H7hDk8TjjnGh1jL3NgNZLRQ_h8jY8/edit?usp=sharing"
CREDENTIALS_FILE = "credentials.json"

BASE_URL = "https://sangtacviet.app"
URL_REALTIME = BASE_URL + "/?find=&minc=0&sort=bookmarked&tag="
URL_TOPWEEK = BASE_URL + "/?find=&minc=0&sort=viewweek&tag="

PAGES = 3          # mỗi trang ~48 truyện -> 3 trang ~144 truyện
MAX_ITEMS = 100    # cắt bớt còn đúng 100 truyện mỗi danh sách
# -----------------

# JS chạy trong trình duyệt để bóc dữ liệu từ các thẻ <a class="booksearch">
EXTRACT_JS = """
() => {
    const parseNum = (t) => {
        if (!t) return 0;
        t = t.trim().toLowerCase().replace(/,/g, '');
        let m = t.match(/([\\d.]+)\\s*([km])?/);
        if (!m) return 0;
        let n = parseFloat(m[1]) || 0;
        if (m[2] === 'k') n *= 1000;
        if (m[2] === 'm') n *= 1000000;
        return Math.round(n);
    };

    // Lấy con số đứng trước 1 icon cụ thể trong khối .info
    const infoBy = (item, iconClass) => {
        for (const sp of item.querySelectorAll('.info span')) {
            if (sp.querySelector('i.' + iconClass)) return parseNum(sp.textContent);
        }
        return 0;
    };

    return Array.from(document.querySelectorAll('a.booksearch')).map(item => {
        const href = item.getAttribute('href') || '';
        // href: https://sangtacviet.app/truyen/{host}/1/{bookid}/
        const parts = href.replace(/https?:\\/\\/[^/]+/, '').split('/').filter(Boolean);
        const bookHost = parts.length >= 4 ? parts[1] : '';
        const bookId   = parts.length >= 4 ? parts[3] : '';

        const title  = (item.querySelector('b.searchbooktitle')?.textContent || '').trim();
        const author = (item.querySelector('span.searchbookauthor')?.textContent || '').trim();
        const img    = item.querySelector('img')?.getAttribute('src') || '';

        const views    = infoBy(item, 'fa-eye');
        const likes    = infoBy(item, 'fa-thumbs-up');
        const chapters = infoBy(item, 'fa-copyright');

        // searchtag đầu là host, tag thứ 2 là trạng thái (Còn Tiếp / Hoàn)
        const tags = Array.from(item.querySelectorAll(':scope > div > span.searchtag'))
                          .map(e => e.textContent.trim());
        const status = tags.length > 1 ? tags[1] : '';

        return { bookId, title, author, bookHost, img, chapters, views, likes, status, href };
    });
}
"""


async def scrape_list(page, base_url, pages=PAGES, max_items=MAX_ITEMS):
    """Cào 1 danh sách (realtime hoặc top tuần) qua nhiều trang."""
    novels = []
    seen = set()

    for p in range(1, pages + 1):
        url = base_url if p == 1 else f"{base_url}&p={p}"
        print(f"➡️  Đang tải trang {p}: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded")
            # Kết quả được render bằng JS -> phải chờ thẻ booksearch xuất hiện
            await page.wait_for_selector("a.booksearch", timeout=30000)
            await page.wait_for_timeout(800)

            items = await page.evaluate(EXTRACT_JS)
        except Exception as e:
            print(f"❌ Lỗi khi tải trang {p}: {e}")
            continue

        if not items:
            print(f"⚠️ Trang {p} không có dữ liệu, dừng lại.")
            break

        new_count = 0
        for it in items:
            if not it["bookId"] or not it["title"]:
                continue
            key = f'{it["bookHost"]}/{it["bookId"]}'
            if key in seen:
                continue
            seen.add(key)
            new_count += 1

            novels.append([
                it["bookId"],       # A - ID truyện
                it["title"],        # B - Tên truyện
                it["author"],       # C - Tác giả
                it["bookHost"],     # D - Nguồn (fanqie / qidian / dich ...)
                it["img"],          # E - Ảnh bìa
                it["chapters"],     # F - Số chương
                it["views"],        # G - Lượt xem
                it["likes"],        # H - Lượt thích
                it["status"],       # I - Trạng thái
                it["href"],         # J - Link truyện
            ])

            if len(novels) >= max_items:
                print(f"✅ Đã đủ {max_items} truyện.")
                return novels

        print(f"   Lấy được {new_count} truyện mới (tổng {len(novels)}).")

    return novels


async def main():
    PROXY_SERVER = os.environ.get("PROXY_SERVER")
    PROXY_USER = os.environ.get("PROXY_USER")
    PROXY_PASS = os.environ.get("PROXY_PASS")

    proxy_settings = None
    if PROXY_SERVER:
        proxy_settings = {
            "server": f"http://{PROXY_SERVER}",
            "username": PROXY_USER,
            "password": PROXY_PASS,
        }
        print(f"--- Đang sử dụng proxy: {PROXY_SERVER} ---")
    else:
        print("--- Không có proxy, chạy trực tiếp ---")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, proxy=proxy_settings)
        context = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
            locale="vi-VN",
        )
        page = await context.new_page()
        page.set_default_timeout(60000)

        try:
            print("Đang kết nối tới Google Sheets...")
            gc = gspread.service_account(filename=CREDENTIALS_FILE)
            sh = gc.open_by_url(GOOGLE_SHEET_NAME)
            print("Kết nối thành công!")

            header = ["ID", "Tên truyện", "Tác giả", "Nguồn", "Ảnh",
                      "Số chương", "Lượt xem", "Lượt thích", "Trạng thái", "Link"]

            def get_ws(name):
                try:
                    ws = sh.worksheet(name)
                except gspread.WorksheetNotFound:
                    ws = sh.add_worksheet(title=name, rows="500", cols="12")
                ws.update(range_name="A1", values=[header])
                return ws

            # --- 1. DANH SÁCH THỜI GIAN THỰC (mới cập nhật) ---
            print("\n=== Đang lấy danh sách THỜI GIAN THỰC ===")
            realtime = await scrape_list(page, URL_REALTIME)
            if realtime:
                ws = get_ws("list_realtime")
                ws.batch_clear(["A2:J1000"])
                ws.update(range_name="A2", values=realtime)
                print(f"✅ Đã ghi {len(realtime)} truyện vào list_realtime.")

            # --- 2. DANH SÁCH TOP ĐỌC TUẦN ---
            print("\n=== Đang lấy danh sách TOP ĐỌC TUẦN ===")
            topweek = await scrape_list(page, URL_TOPWEEK)
            if topweek:
                ws = get_ws("list_top")
                ws.batch_clear(["A2:J1000"])
                ws.update(range_name="A2", values=topweek)
                print(f"✅ Đã ghi {len(topweek)} truyện vào list_top.")

        except Exception as e:
            print(f"❌ Đã xảy ra lỗi nghiêm trọng: {e}")
            try:
                os.makedirs("screenshots", exist_ok=True)
                await page.screenshot(path="screenshots/00_ERROR.png", full_page=True)
                print("Đã chụp ảnh màn hình lỗi.")
            except Exception as se:
                print(f"Không thể chụp ảnh màn hình: {se}")

        finally:
            print("\nQuá trình đã hoàn tất. Đóng trình duyệt.")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
