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
