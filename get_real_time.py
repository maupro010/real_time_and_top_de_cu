import asyncio
from playwright.async_api import async_playwright
import os
import csv
import gspread
import re

# --- THÔNG TIN ĐĂNG NHẬP ---
LOGIN_EMAIL = os.environ.get('LOGIN_EMAIL')
LOGIN_PASSWORD = os.environ.get('LOGIN_PASSWORD')
# ------------------------------

# --- THÔNG TIN GOOGLE SHEET ---
GOOGLE_SHEET_NAME = "https://docs.google.com/spreadsheets/d/1rCGTw4GdGlR4K-H7hDk8TjjnGh1jL3NgNZLRQ_h8jY8/edit?usp=sharing"
CREDENTIALS_FILE = "credentials.json"
# ------------------------------
async def scrape_novel_top(page):    
    novels = []
    for i in range(2, 22):
        img_selector = f'#app > div:nth-child(2) > main > div > div.md\\:col-span-2.space-y-8 > div:nth-child(4) > div.grid.grid-cols-1.gap-y-6 > div:nth-child({i}) > div.flex-shrink-0 > a > img'
        title_selector = f'#app > div:nth-child(2) > main > div > div.md\\:col-span-2.space-y-8 > div:nth-child(4) > div.grid.grid-cols-1.gap-y-6 > div:nth-child({i}) > div.flex-grow.space-y-2 > div.flex.items-center.space-x-2 > a'
        author_selector = f'#app > div:nth-child(2) > main > div > div.md\\:col-span-2.space-y-8 > div:nth-child(4) > div.grid.grid-cols-1.gap-y-6 > div:nth-child({i}) > div.flex-grow.space-y-2 > div.flex.justify-between.space-x-2.pt-1 > div > span'
        max_selector = f'#app > div:nth-child(2) > main > div > div.md\\:col-span-2.space-y-8 > div:nth-child(4) > div.grid.grid-cols-1.gap-y-6 > div:nth-child({i}) > div.flex-grow.space-y-2 > div.flex.justify-between.space-x-2.pt-1 > span'

        try:
            # 1. Ảnh: Nằm trong div.flex-shrink-0
            img = await page.locator(img_selector).get_attribute('src')
            
            # 2. Tiêu đề: Thẻ a trong div.flex.items-center.space-x-2
            title = await page.locator(title_selector).inner_text()

            url = await page.locator(title_selector).get_attribute('href')
            
            # 3. Tác giả: Thẻ span đầu tiên trong cụm div cuối
            author = await page.locator(author_selector).inner_text()
            
            # 4. Số chương: Thẻ span cuối cùng (thường là sibling của div chứa author)
            max_chapter_text = await page.locator(max_selector).inner_text()

            novels.append([
                url.strip(),
                title.strip(),
                author.strip(),
                '',                
                img.strip(),
                max_chapter_text.strip(),
                ''
            ])
        except Exception as e:
            print(f"❌ Đã xảy ra lỗi nghiêm trọng: {e}")
            continue
    return novels

async def scrape_novel_list(page):    
    novels = []
    for i in range(2, 102):
        img_selector = f'#app > div:nth-child(2) > main > div > div > div:nth-child(4) > div.grid.grid-cols-1.gap-y-6 > div:nth-child({i}) > div.flex-shrink-0 > a > img'
        title_selector = f'#app > div:nth-child(2) > main > div > div > div:nth-child(4) > div.grid.grid-cols-1.gap-y-6 > div:nth-child({i}) > div.flex-grow.space-y-2 > div.flex.items-center.justify-between.space-x-2 > div.flex.items-center.space-x-2 > a'
        author_selector = f'#app > div:nth-child(2) > main > div > div > div:nth-child(4) > div.grid.grid-cols-1.gap-y-6 > div:nth-child({i}) > div.flex-grow.space-y-2 > div.flex.justify-between.space-x-2.pt-1 > div > span'
        max_selector = f'#app > div:nth-child(2) > main > div > div > div:nth-child(4) > div.grid.grid-cols-1.gap-y-6 > div:nth-child({i}) > div.flex-grow.space-y-2 > div.flex.justify-between.space-x-2.pt-1 > span'

        try:
            # 1. Ảnh: Nằm trong div.flex-shrink-0
            img = await page.locator(img_selector).get_attribute('src')
            
            # 2. Tiêu đề: Thẻ a trong div.flex.items-center.space-x-2
            title = await page.locator(title_selector).inner_text()

            url = await page.locator(title_selector).get_attribute('href')
            
            # 3. Tác giả: Thẻ span đầu tiên trong cụm div cuối
            author = await page.locator(author_selector).inner_text()
            
            # 4. Số chương: Thẻ span cuối cùng (thường là sibling của div chứa author)
            max_chapter_text = await page.locator(max_selector).inner_text()

            novels.append([
                url.strip(),
                title.strip(),
                author.strip(),
                '',                
                img.strip(),
                max_chapter_text.strip(),
                ''
            ])
        except Exception as e:
            print(f"❌ Đã xảy ra lỗi nghiêm trọng: {e}")
            continue
    return novels

async def scrape_novel_detail(page):
    desc_selector = '#synopsis > div.text-gray-600.dark\\:text-gray-300.py-4.px-2.md\\:px-1.text-base.break-words'
    id_selector = '#app > div:nth-child(2) > div > main > div.space-y-5 > div.block.md\\:flex > div.mb-4.mx-auto.text-center.md\\:mx-0.md\\:text-left > div.space-x-4.mb-6.md\\:mb-8 > div'
    id_selector2 = '#app > div:nth-child(2) > main > div.space-y-5 > div.block.md\\:flex > div.mb-4.mx-auto.text-center.md\\:mx-0.md\\:text-left > div.space-x-4.mb-6.md\\:mb-8 > div'
    
    # Khởi tạo tất cả các biến với giá trị mặc định là chuỗi rỗng
    desc = ""
    target_id = ""

    try:
        try:
            desc = await page.locator(desc_selector).inner_text(timeout=30000)
        except Exception as e:
            print(f"⚠️ Lỗi khi lấy desc: {e}")        
        
        # --- Lấy ID (data-x-data) ---
        try:
            data_x_data = await page.locator(id_selector2).get_attribute("data-x-data")
            if data_x_data:
                match = re.search(r'\(([^)]+)\)', data_x_data)
                if match:
                    target_id = match.group(1).strip()
                else:
                    print("⚠️ Không tìm thấy ID trong thuộc tính data-x-data.")
            else:
                print("⚠️ Không tìm thấy thuộc tính data-x-data.")
        except:
            try:
                data_x_data = await page.locator(id_selector).get_attribute("data-x-data")
                if data_x_data:
                    match = re.search(r'\(([^)]+)\)', data_x_data)
                    if match:
                        target_id = match.group(1).strip()
                    else:
                        print("⚠️ Không tìm thấy ID trong thuộc tính data-x-data.")
                else:
                    print("⚠️ Không tìm thấy thuộc tính data-x-data.")
            except Exception as e:
                print(f"⚠️ Lỗi khi lấy ID (data-x-data): {e}")
        
        # Trả về dictionary, .strip() bây giờ đã an toàn vì tất cả đều là chuỗi
        return {
            "desc": desc.strip(), 
            "id": target_id.strip()
        }

    except Exception as e:
        # Khối except bên ngoài này sẽ bắt các lỗi thảm họa (ví dụ: page bị đóng)
        print(f"❌ Lỗi nghiêm trọng khi lấy chi tiết truyện: {e}")
        return None

async def main():
    """
    Hàm chính điều khiển toàn bộ quá trình: đăng nhập, duyệt và lưu chương.
    """
    # Lấy thông tin proxy từ biến môi trường
    PROXY_SERVER = os.environ.get('PROXY_SERVER')
    PROXY_USER = os.environ.get('PROXY_USER')
    PROXY_PASS = os.environ.get('PROXY_PASS')

    proxy_settings = None
    if PROXY_SERVER:
        proxy_settings = {
            "server": f"http://{PROXY_SERVER}",
            "username": PROXY_USER,
            "password": PROXY_PASS
        }
        print(f"--- Đang sử dụng proxy: {PROXY_SERVER} ---")
    else:
        print("--- Không tìm thấy thông tin proxy, chạy không qua proxy ---")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy=proxy_settings
        )
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(60000) # 60 giây
        try:
            # --- PHẦN 1: ĐĂNG NHẬP (Chỉ chạy một lần) ---
            print("Bắt đầu quá trình đăng nhập...")
            await page.goto("https://metruyencv.com", wait_until="domcontentloaded")
            
            menu_icon_locator = page.locator('svg:has(path[d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"])')
            await menu_icon_locator.wait_for(state="visible")
            await menu_icon_locator.click()
            await page.get_by_role("button", name="Đăng nhập").click()
            await page.get_by_placeholder("email").fill(LOGIN_EMAIL)
            await page.get_by_placeholder("password").fill(LOGIN_PASSWORD)
            await page.get_by_role("button", name="Đăng nhập").click()
            print("Đăng nhập thành công!")
            # --- PHẦN 0: KẾT NỐI VÀ KIỂM TRA GOOGLE SHEET ---
            print("Đang kết nối tới Google Sheets...")
            gc = gspread.service_account(filename=CREDENTIALS_FILE)
            sh = gc.open_by_url(GOOGLE_SHEET_NAME)
            print("Kết nối thành công!")

            # --- XỬ LÝ TRANG THỜI GIAN THỰC ---
            print("Đang lấy danh sách truyện thời gian thực...")
            await page.goto("https://metruyencv.com/thoi-gian-thuc", wait_until="domcontentloaded")


            # Lấy dữ liệu từ hàm đã viết
            novel_list_data = await scrape_novel_list(page)            

            for novel in novel_list_data:
                response = await page.goto(novel[0], wait_until="domcontentloaded")
                if response and response.status == 404:
                    continue
                scraped_data = await scrape_novel_detail(page)
                if scraped_data:
                    novel[3] = scraped_data['desc']
                    novel.append(scraped_data['id'])

            if novel_list_data:
                try:
                    # Mở hoặc tạo sheet list_realtime
                    try:
                        ws_realtime = sh.worksheet("list_realtime")
                    except gspread.WorksheetNotFound:
                        ws_realtime = sh.add_worksheet(title="list_realtime", rows="101", cols="8")
                        ws_realtime.append_row(['Url', 'Title', 'Author', 'Desc', 'Image URL', 'Max Chapter', 'Update', 'ID'])

                    # Ghi dữ liệu (Ghi đè hoặc nối tiếp tùy bạn, ở đây là ghi nối tiếp)
                    ws_realtime.update(range_name='A2', values=novel_list_data)
                    print(f"✅ Đã cập nhật {len(novel_list_data)} truyện vào sheet list_realtime")
                except Exception as e:
                    print(f"❌ Lỗi khi ghi Sheet: {e}")


            # --- XỬ LÝ TRANG TOP ---
            print("Đang lấy danh sách truyện top...")
            await page.goto("https://metruyencv.com/xep-hang/de-cu", wait_until="domcontentloaded")

            for i in range(5):
                # Lấy dữ liệu từ hàm đã viết
                novel_list_data = await scrape_novel_top(page)            

                for novel in novel_list_data:
                    response = await page.goto(novel[0], wait_until="domcontentloaded")
                    if response and response.status == 404:
                        continue
                    scraped_data = await scrape_novel_detail(page)
                    if scraped_data:
                        novel[3] = scraped_data['desc']
                        novel.append(scraped_data['id'])

                if novel_list_data:
                    try:
                        # Mở hoặc tạo sheet list_realtime
                        try:
                            ws_realtime = sh.worksheet("list_top")
                        except gspread.WorksheetNotFound:
                            ws_realtime = sh.add_worksheet(title="list_top", rows="101", cols="8")
                            ws_realtime.append_row(['Url', 'Title', 'Author', 'Desc', 'Image URL', 'Max Chapter', 'Update' 'ID'])

                        # Ghi dữ liệu (Ghi đè hoặc nối tiếp tùy bạn, ở đây là ghi nối tiếp)
                        ws_realtime.update(range_name=f'A{20*i+2}', values=novel_list_data)
                        print(f"✅ Đã cập nhật {len(novel_list_data)} truyện vào sheet list_top")
                    except Exception as e:
                        print(f"❌ Lỗi khi ghi Sheet: {e}")
                if i < 4:
                    await page.goto("https://metruyencv.com/xep-hang/de-cu", wait_until="domcontentloaded")
                    for _ in range(i+1):
                        await page.locator('svg:has(path[d="M9 6l6 6l-6 6"])').click()

        except Exception as e:
            print(f"❌ Đã xảy ra lỗi nghiêm trọng: {e}")
            try:
                await page.screenshot(path='screenshots/00_ERROR.png')
                print("Đã chụp ảnh màn hình lỗi.")
            except Exception as screenshot_error:
                print(f"Không thể chụp ảnh màn hình: {screenshot_error}")

        finally:
            print("\nQuá trình đã hoàn tất. Đóng trình duyệt.")
            await browser.close()



# Chạy script
if __name__ == "__main__":
    asyncio.run(main())
