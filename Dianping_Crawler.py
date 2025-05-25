# -*- coding: utf-8 -*-
import time
import random
import re
import pprint
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium_stealth import stealth
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import quote # 用于URL编码关键词
import requests # 用于调用百度地图API
import json # 用于处理API返回的JSON数据

# ==============================================================================
# --- 全局配置 ---
# ==============================================================================
CONFIG = {
    # --- 爬取目标配置 ---
    "CITY_ID": "1",
    "KEYWORD": "奶茶",
    "SEARCH_FILTER_PREFIX": "10_",
    "DIANPING_DOMAIN": "https://www.dianping.com",

    # --- ChromeDriver 配置 ---
    "LOCAL_CHROME_DRIVER_PATH": r"C:\136.0.7103.49 chromedriver-win64\chromedriver-win64\chromedriver.exe", # 示例路径，请修改为你的实际路径

    # --- Cookie 配置 ---
    # !!! 重要：请在此处填入你从浏览器获取的完整、有效的 Cookie 字符串 !!!
    "DIANPING_COOKIE_STRING": "_lxsdk_cuid=19608ddb8afc8-09191d25ea2132-26011c51-168000-19608ddb8afc8; _lxsdk=19608ddb8afc8-09191d25ea2132-26011c51-168000-19608ddb8afc8; _hc.v=e184a821-8661-a29d-6d44-1adae5f64889.1743905471; ctu=4561f61fb652f99b901515db4a20a3d346b19722abb437edeb468ae1e71e4c70; s_ViewType=10; cityid=2; default_ab=myinfo%3AA%3A1%7CshopList%3AC%3A5; fspop=test; WEBDFPID=xvx3ww54uv155918yz98wzz048y0v11280391wwv43897958840xwxu3-1747809156616-1743905479008GEQIEKCfd79fef3d01d5e9aadc18ccd4d0c95073324; Hm_lvt_602b80cf8079ae6591966cc70a3940e7=1747289200,1747290086,1747290134,1747722820; HMACCOUNT=B3258419914A351E; cy=1; cye=shanghai; __CACHE@is_login=true; __CACHE@referer=https://www.dianping.com/search/keyword/1/0_%E5%A5%B6%E8%8C%B6; logan_custom_report=; _lx_utm=utm_source%3Dgoogle%26utm_medium%3Dorganic; logan_session_token=n34ihq0uszmpeau57r7t; qruuid=b5232b52-d34c-42a7-9a0c-eeb2ef2ee2ba; dplet=4adec197a8a0f5e23ee669f3f9ce0e45; dper=0202c41fbfa8cc85ceadcad5fc89f721f0caf536a4229f3703445b1fa8c3db5e559b20804fd9712b8ab6ce5871c68e38321b7970162173ec7f6e000000006f2900000cf68aa96c8565f11c42fbda332659e47d3561476ca5f88bec597944607a8ada463409759e07c08317a39cbc0b5b2286; ll=7fd06e815b796be3df069dec7836c3df; ua=Windymui; _lxsdk_s=196edcf6b2c-841-c16-293%7C%7C80; Hm_lpvt_602b80cf8079ae6591966cc70a3940e7=1747746580", # 例如："_lxsdk_cuid=xxx; _lxsdk=xxx; ..."

    # --- 爬取页数配置 ---
    "START_PAGE": 10,
    "MAX_PAGES_TO_SCRAPE": 46,

    # --- 评论抓取配置 ---
    "MAX_REVIEWS_TO_SCRAPE_PER_SHOP": 3, # 每个店铺详情页最多抓取多少条评论

    # --- 反爬虫相关配置 ---
    "SLIDER_MAX_RETRY": 2,
    "PAGE_LOAD_TIMEOUT": 30,
    "DETAIL_PAGE_CORE_ELEMENT_TIMEOUT": 15,
    "SAFE_GET_PAGE_MAX_RETRY": 2,
    "DETAIL_PAGE_UA_ROTATION_LIMIT": 5,
    "DETAIL_PAGE_REFRESH_WAIT_S1": 2.5,
    "DETAIL_PAGE_REFRESH_WAIT_S2": 3.0,

    # --- 百度地图Geocoding API配置 ---
    # !!! 重要：请在此处填入你申请的、已启用地理编码服务（正向）的百度地图开发者AK (API Key) !!!
    # !!! 确保此AK对应的应用在百度地图开放平台已开启“地理编码服务”，并检查IP白名单等设置 !!!
    "BAIDU_MAPS_API_KEY": "gt3WT43O0R2u5EdU2b56IeM3PUM1zG2t", # 你提供的AK，请确保其有效性及配置正确
    "GEOCODING_REQUEST_DELAY": 1,

    # --- User-Agent 列表 ---
    "USER_AGENTS": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Opera/108.0.0.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
}

DIANPING_SEARCH_URL = f"{CONFIG['DIANPING_DOMAIN']}/search/keyword/{CONFIG['CITY_ID']}/{CONFIG['SEARCH_FILTER_PREFIX']}{quote(CONFIG['KEYWORD'])}"

chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1280,800")
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-popup-blocking')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-running-insecure-content')
chrome_options.add_argument("--disable-infobars")
target_category = "茶饮果汁" # 目标分类名称

# ==============================================================================
# --- 百度地图Geocoding函数 ---
# ==============================================================================
def geocode_address_baidu(address, api_key):
    """使用百度地图API将地址文本转换为经纬度"""
    if not address or address == 'N/A':
        print(f"提供的地址无效 ('{address}')，跳过地理编码。")
        return None, None
    if "YOUR_BAIDU_MAPS_API_KEY_HERE" in api_key or not api_key:
        print(f"百度地图API Key未正确配置 (或仍为占位符)，跳过地址 '{address}' 的地理编码。")
        return None, None

    host = "https://api.map.baidu.com"
    uri = "/geocoding/v3"
    request_url = host + uri
    params = {"address": address, "output": "json", "ak": api_key}

    try:
        response = requests.get(request_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == 0:
            location = data.get("result", {}).get("location")
            if location and "lng" in location and "lat" in location:
                return location["lng"], location["lat"]
            else:
                print(f"地址 '{address}' Geocoding成功，但未返回有效经纬度。响应: {data}")
                return None, None
        else:
            error_message = data.get('message', '未知错误')
            status_code = data.get('status', 'N/A')
            print(f"百度地图API错误 (地址: '{address}'): status={status_code}, message='{error_message}'")
            if status_code == 240: # 特别处理服务禁用错误
                print("   错误提示：'APP 服务被禁用'。请务必检查百度地图开放平台AK配置：")
                print(f"     1. AK ('{api_key}') 是否正确填写且有效？")
                print("     2. AK对应的应用是否已开启“地理编码”服务权限？")
                print("     3. 是否有IP白名单限制（若有，当前机器IP是否已添加）？")
                print("     4. 调用配额是否充足？")
            return None, None
    except requests.exceptions.Timeout:
        print(f"请求百度地图API超时 (地址: '{address}')")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"请求百度地图API时发生网络错误 (地址: '{address}'): {e}")
        return None, None
    except json.JSONDecodeError:
        print(f"解析百度地图API响应JSON时出错 (地址: '{address}'), 响应内容: {response.text[:200]}...")
        return None, None
    except Exception as e_geo:
        print(f"Geocoding地址 '{address}' 时发生未知错误: {type(e_geo).__name__} - {e_geo}")
        return None, None

# ==============================================================================
# --- 辅助函数 ---
# ==============================================================================
def inject_cookies(driver, cookie_string, domain):
    driver.get(f"{domain}/")
    human_sleep(0.5,0.2,1)
    for pair in cookie_string.split(";"):
        if "=" not in pair: continue
        k, v = pair.strip().split("=", 1)
        try: driver.add_cookie({"name": k, "value": v, "path": "/"})
        except Exception as e: print(f"添加 Cookie {k}={v} 失败: {e}")

def safe_get_page(driver, url, max_retry=CONFIG["SAFE_GET_PAGE_MAX_RETRY"], is_list_page=True):
    for attempt in range(max_retry + 1):
        try:
            if attempt > 0 and is_list_page:
                new_ua = random.choice(CONFIG["USER_AGENTS"])
                print(f"列表页加载异常 (尝试 {attempt+1})，更换UA至: {new_ua[:60]}... 并刷新。")
                driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": new_ua})
                human_sleep(0.3, 0.1, 0.8); driver.refresh(); human_sleep(1.5, 1, 3)
            driver.get(url)
            page_title = driver.title.lower()
            page_source_sample = driver.page_source.lower()[:1000]
            current_url_val = driver.current_url
            if "403" not in page_title and "forbidden" not in page_source_sample and \
               "verify.meituan.com" not in current_url_val and "error" not in page_title:
                return True
            print(f"页面加载异常 (尝试 {attempt + 1}/{max_retry + 1}): '{page_title}', URL: {current_url_val}")
            if "verify.meituan.com" in current_url_val:
                print("  检测到跳转至验证页面，尝试解决...")
                if solve_slider_captcha(driver):
                    print("  滑块验证通过后，重新检查当前页面状态。")
                    if "verify.meituan.com" not in driver.current_url and "403" not in driver.title.lower(): return True
                else: print("  滑块验证失败或需人工介入。")
        except TimeoutException: print(f"页面加载超时 (尝试 {attempt + 1}): {url}")
        except Exception as e: print(f"访问页面 {url} 时发生未知错误 (尝试 {attempt + 1}): {e}")
        if attempt < max_retry: human_sleep(mean=3 if is_list_page else 1.5, min_delay=2 if is_list_page else 1, max_delay=5 if is_list_page else 3)
    print(f"多次尝试后 ({max_retry + 1} 次) 仍无法成功加载页面: {url}")
    return False

def safe_get_text(element, selector, default='N/A'):
    try:
        tag = element.select_one(selector)
        return tag.get_text(strip=True) if tag else default
    except Exception: return default

def safe_get_attribute(element, selector, attribute, default='N/A'):
    try:
        tag = element.select_one(selector)
        return tag.get(attribute, default) if tag else default
    except Exception: return default

def extract_first_number(text):
    if not text: return None
    text_cleaned = str(text).replace(',', '').replace('￥', '').replace('¥', '').replace('/人', '').replace('条评价', '').replace('条', '').strip()
    match = re.search(r'(\d+(\.\d+)?)', text_cleaned)
    return float(match.group(1)) if match else None

def parse_sub_scores(text):
    scores = {'口味': None, '环境': None, '服务': None}
    if not text or text == 'N/A': return scores
    try:
        taste_match = re.search(r'口味[:：\s]*([\d.]+)', text)
        env_match = re.search(r'环境[:：\s]*([\d.]+)', text)
        service_match = re.search(r'服务[:：\s]*([\d.]+)', text)
        if taste_match: scores['口味'] = float(taste_match.group(1))
        if env_match: scores['环境'] = float(env_match.group(1))
        if service_match: scores['服务'] = float(service_match.group(1))
    except Exception as e: print(f"解析子评分时出错: {e}, 原始文本: {text}")
    return scores

def safe_get_all_texts(element, selector, default=None):
    if default is None: default = []
    try:
        tags = element.select(selector)
        texts = [tag.get_text(strip=True) for tag in tags if hasattr(tag, 'name') and tag.name not in ['script', 'style']]
        return [text for text in texts if text]
    except Exception: return default

def human_sleep(mean=4.5, min_delay=3.0, max_delay=8.0):
    delay = np.random.exponential(mean)
    actual_delay = max(min_delay, min(delay, max_delay))
    time.sleep(actual_delay)

def solve_slider_captcha(driver, max_retry=CONFIG["SLIDER_MAX_RETRY"]):
    # (此函数与上一版本相同，保持不变)
    try:
        for i in range(max_retry):
            if "verify.meituan.com" not in driver.current_url: return True
            print(f"尝试自动滑块验证 (第 {i+1}/{max_retry} 次)...")
            human_sleep(mean=1.2, min_delay=0.5, max_delay=2)
            try:
                slider_button = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.slider > span.slider-btn, .J_slider .btn_slide")))
                slider_track_element = driver.find_element(By.CSS_SELECTOR, "div.slider, .J_slider")
                track_width = slider_track_element.size['width']
                move_distance = track_width - slider_button.size['width'] - random.randint(5,15)
                if move_distance <=0: move_distance = track_width * 0.8
                action = ActionChains(driver).click_and_hold(slider_button).pause(random.uniform(0.1, 0.3))
                offsets = []
                remaining_distance = move_distance
                while remaining_distance > 0:
                    segment = random.uniform(remaining_distance * 0.1, remaining_distance * 0.4); segment = min(segment, remaining_distance)
                    offsets.append(segment); remaining_distance -= segment
                for offset_val in offsets: action.move_by_offset(offset_val, random.randint(-5, 5)).pause(random.uniform(0.05, 0.2))
                action.release().perform()
            except Exception as e_slide:
                print(f"拖动滑块过程中发生错误: {e_slide}")
                try: refresh_button = driver.find_element(By.CSS_SELECTOR, ".refresh-btn, .J_reload"); refresh_button.click(); human_sleep(1,0.5,2)
                except NoSuchElementException: pass
                continue
            human_sleep(mean=2, min_delay=1, max_delay=3)
            if "verify.meituan.com" not in driver.current_url: print("→ 自动滑块验证成功！"); return True
            else:
                error_msg_element = driver.find_elements(By.CSS_SELECTOR, ".error-msg, .validate-info")
                if error_msg_element and error_msg_element[0].is_displayed(): print(f"滑块验证提示: {error_msg_element[0].text}")
        print("→ 自动滑块多次尝试失败，需要人工介入。")
        input("请在浏览器窗口手动拖动滑块通过验证后，再回到终端按 Enter 继续...")
        if "verify.meituan.com" not in driver.current_url: print("人工验证成功。"); return True
        else: print("人工验证后似乎仍停留在验证页面。"); return False
    except Exception as e:
        print(f"处理滑块验证码时发生异常: {e}")
        input("滑块验证出现未知错误，请手动处理后按 Enter 继续...")
        return "verify.meituan.com" not in driver.current_url


def random_human_action(driver):
    # (此函数与上一版本相同，保持不变)
    try:
        action_type = random.choice(['scroll', 'small_scroll', 'hover'])
        if action_type == 'scroll': driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {random.uniform(0.2, 0.8)});")
        elif action_type == 'small_scroll': driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300) * random.choice([-1,1])});")
        elif action_type == 'hover':
            elements_to_hover = driver.find_elements(By.CSS_SELECTOR, "a[href], img, .shop-name, .comment")
            if elements_to_hover:
                target_element = random.choice(elements_to_hover)
                if target_element.is_displayed() and target_element.is_enabled(): ActionChains(driver).move_to_element(target_element).pause(random.uniform(0.3,0.8)).perform()
    except StaleElementReferenceException: pass
    except Exception: pass

# ==============================================================================
# --- 评论文本提取辅助函数 ---
# ==============================================================================
def extract_review_text_from_body(review_body_data):
    """从 reviewBody JSON 结构中提取纯文本评论。"""
    if not review_body_data or not isinstance(review_body_data, dict):
        return ""

    texts = []
    # reviewBody 通常有一个顶层子元素，其 children 包含实际内容
    # 例如: reviewBody: { "children": [{ "name": "div", "children": [HERE] }] }
    top_children = review_body_data.get("children")
    if top_children and isinstance(top_children, list) and len(top_children) > 0:
        content_children = top_children[0].get("children")
        if content_children and isinstance(content_children, list):
            for child in content_children:
                if child.get("type") == "text" and "text" in child:
                    texts.append(child["text"])
                elif child.get("type") == "node" and child.get("name") == "img" and "attrs" in child:
                    # 可以选择性地保留图片表情的 alt 文本
                    alt_text = child["attrs"].get("alt", "")
                    if alt_text:
                        texts.append(alt_text)
                # 忽略 <br> 等其他节点，或按需处理
    return "".join(texts).strip()


# ==============================================================================
# --- 页面解析函数 ---
# ==============================================================================
def parse_dianping_search_list(soup, domain):
    # (与上一版本基本一致，主要确保 review_count 和 category 提取)
    shop_list_on_page = []
    shop_list_container_div = soup.select_one('div#shop-all-list')
    if not shop_list_container_div:
        shop_list_ul = soup.select_one('ul.shop-list, ul.shop-listJ')
        if not shop_list_ul: print("错误：也未能找到备用店铺列表容器。"); return []
        shop_items = shop_list_ul.find_all('li', recursive=False)
    else:
        shop_ul = shop_list_container_div.select_one('ul')
        if not shop_ul: print("错误：在 div#shop-all-list 中未找到 ul 列表。"); return []
        shop_items = shop_ul.find_all('li', recursive=False)
    if not shop_items: print("错误：未能找到任何店铺列表项 (li)。"); return []

    for item_idx, item in enumerate(shop_items):
        link_tag = item.select_one('div.tit a[data-shopid]')
        if not link_tag:
            link_tag = item.select_one('a.shopname[data-shopid], a.shop-name[data-shopid]')
            if not link_tag:
                link_tag = item.select_one('a[data-shopid]')
                if not link_tag: continue
        shop_id = link_tag.get('data-shopid', 'N/A'); href = link_tag.get('href', 'N/A')
        if href and href.startswith('/'): href = f"{domain}{href}"
        elif not href.startswith('http'): href = 'N/A'
        if shop_id == 'N/A' or href == 'N/A': continue
        shop_name_from_link = link_tag.get_text(strip=True)
        shop_name_h4 = safe_get_text(item, 'div.txt h4, h4.shop-name')
        name_list_page = shop_name_h4 if shop_name_h4 != 'N/A' else shop_name_from_link
        if not name_list_page: name_list_page = 'N/A'

        review_count_text = safe_get_text(item, 'a.review-num b')
        review_count = extract_first_number(review_count_text)
        
        # 确保 category 的提取选择器是有效的
        category = safe_get_text(item, 'div.tag-addr span.tag:nth-of-type(1), div.tag-addr a:nth-of-type(1) span.tag, span.tag.item-type')


        shop_info = {
            'name_list_page': name_list_page, 'link': href, 'shop_id': shop_id, 'rating': 'N/A',
            'review_count': review_count,
            'avg_price': extract_first_number(safe_get_text(item, 'a.mean-price b')),
            'category': category, # 使用上面提取的 category
            'region': safe_get_text(item, 'div.tag-addr span.tag:nth-of-type(2), div.tag-addr a:nth-of-type(2) span.tag, span.tag.item-region'),
            'recommended_dishes': ", ".join(safe_get_all_texts(item, 'div.recommend a.recommend-click, span.recommend')),
            'name': 'N/A', 'operating_hours': 'N/A', 'address': 'N/A', 'lat': None, 'lng': None,
            'sub_scores': {'口味': None, '环境': None, '服务': None},
            'is_chain': 0, 'has_group_purchase_套餐': 0,
            'reviews_data': [] # 改为存储结构化评论数据
            }
        shop_list_on_page.append(shop_info)
    return shop_list_on_page

def scrape_additional_details(driver, shop_info_from_list, domain, detail_timeout):
    shop_info = shop_info_from_list.copy()
    detail_link = shop_info.get('link')

    if not detail_link or detail_link == 'N/A' or not detail_link.startswith('http'):
        print(f"店铺 {shop_info.get('name_list_page', shop_info.get('shop_id'))} 缺少有效详情链接 ({detail_link})，跳过。")
        return shop_info

    shop_id = shop_info.get('shop_id')
    print(f"\n---\n访问店铺 ID: {shop_id} ({shop_info.get('name_list_page', 'N/A')})")

    main_window_handle = driver.current_window_handle
    try:
        driver.execute_script("window.open(arguments[0], '_blank');", detail_link)
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(len(driver.window_handles)))
        new_window_handle = [handle for handle in driver.window_handles if handle != main_window_handle][-1]
        driver.switch_to.window(new_window_handle)

        is_detail_page_successfully_loaded = False
        ua_rotation_limit = CONFIG.get("DETAIL_PAGE_UA_ROTATION_LIMIT", 5)
        core_page_element_selector = "h1.shop-name, span.shopName, div.shop-name, .main, .shop-crumbs, #aside, .shop-header"

        for ua_attempt_num in range(ua_rotation_limit + 1):
            action_taken_this_attempt = False

            if ua_attempt_num == 0:
                print(f"   首次尝试加载详情页: {detail_link}")
                driver.get(detail_link)
                human_sleep(1.5, 1, 2.5)
                action_taken_this_attempt = True
            else:
                print(f"   详情页加载重试 {ua_attempt_num}/{ua_rotation_limit}...")
                if "verify.meituan.com" in driver.current_url :
                    print(f"     仍停留在验证页面，尝试返回原详情页链接: {detail_link}")
                    driver.get(detail_link); human_sleep(1,0.5,2)
                    if "verify.meituan.com" in driver.current_url: print("     返回原链接后仍是验证页，继续UA更换流程。")

                current_ua_from_browser = driver.execute_script("return navigator.userAgent;")
                possible_new_uas = [ua for ua in CONFIG["USER_AGENTS"] if ua != current_ua_from_browser] or CONFIG["USER_AGENTS"]
                new_ua = random.choice(possible_new_uas)
                print(f"     更换UA至: {new_ua[:60]}...")
                driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": new_ua})
                human_sleep(0.2, 0.1, 0.5)
                action_taken_this_attempt = True

                # --- Modified Refresh Logic ---
                print(f"     执行第一次刷新...")
                driver.refresh()
                human_sleep(CONFIG.get("DETAIL_PAGE_REFRESH_WAIT_S1", 2.0), 1.0, 3.0)

                page_title_after_first_refresh = driver.title.lower()
                current_url_after_first_refresh = driver.current_url
                if "verify.meituan.com" not in current_url_after_first_refresh and \
                   "403" not in page_title_after_first_refresh and "error" not in page_title_after_first_refresh:
                    try:
                        WebDriverWait(driver, detail_timeout // 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, core_page_element_selector)))
                        print(f"     第一次刷新后内容加载成功。")
                        is_detail_page_successfully_loaded = True; break
                    except TimeoutException:
                        print(f"     第一次刷新后核心元素未找到。将执行第二次刷新。")
                else:
                    print(f"     第一次刷新后页面状态仍不佳 (URL: {current_url_after_first_refresh}, Title: {page_title_after_first_refresh})。执行第二次刷新。")

                if not is_detail_page_successfully_loaded: # 只有在第一次刷新不成功时才执行第二次
                    print(f"     执行第二次刷新...")
                    driver.refresh()
                    human_sleep(CONFIG.get("DETAIL_PAGE_REFRESH_WAIT_S2", 2.5), 1.5, 3.5)

            if not action_taken_this_attempt and ua_attempt_num > 0:
                print("警告：UA轮换后没有执行加载/刷新操作，逻辑可能存在问题。")

            page_title = driver.title.lower()
            page_source_sample = driver.page_source.lower()[:1000]
            current_url = driver.current_url

            if "verify.meituan.com" in current_url:
                print("   验证页面被检测到。尝试自动解决滑块...")
                if solve_slider_captcha(driver):
                    print("   滑块验证流程结束。重新检查页面状态...")
                    current_url = driver.current_url; page_title = driver.title.lower()
                    if "verify.meituan.com" in current_url: print("   解决滑块后仍停留在验证页面。"); continue
                else: print("   滑块验证失败或需人工干预但未确认。"); continue

            if "403" in page_title or "forbidden" in page_source_sample or "error" in page_title or "invalid request" in page_source_sample:
                print(f"   页面标题或内容指示错误。尝试次数 {ua_attempt_num + 1}。"); continue

            try:
                WebDriverWait(driver, detail_timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, core_page_element_selector)))
                print(f"   详情页内容加载成功 (总尝试 {ua_attempt_num + 1})。")
                is_detail_page_successfully_loaded = True; break
            except TimeoutException:
                print(f"   详情页核心元素未在超时 ({detail_timeout}s) 内找到 (总尝试 {ua_attempt_num + 1})。")
                if ua_attempt_num >= ua_rotation_limit:
                    print(f"!! 达到最大UA轮换次数 ({ua_rotation_limit})，仍无法加载店铺 {shop_id} 详情。")

        if not is_detail_page_successfully_loaded:
            print(f"!! 最终无法成功加载店铺 {shop_id} 的详情页 ({detail_link})。")
            if driver.current_window_handle != main_window_handle: driver.close()
            driver.switch_to.window(main_window_handle); return shop_info

        random_human_action(driver); human_sleep(mean=1, min_delay=0.5, max_delay=2)
        current_page_html = driver.page_source
        detail_soup = BeautifulSoup(current_page_html, 'html.parser')

        # --- 基本信息解析 (与之前版本类似) ---
        shop_name_tag = detail_soup.select_one('h1.shop-name, span.shopName.wx-text, .shopDesc .shopWname, div.shop-name .name, .shop-title .name')
        if shop_name_tag:
            actual_shop_name = shop_name_tag.get_text(strip=True); shop_info['name'] = actual_shop_name
            if "(" in actual_shop_name and ")" in actual_shop_name and ("店" in actual_shop_name or len(actual_shop_name.split('(',1)[0].strip()) < (len(actual_shop_name.replace('(','').replace(')','')) - 2)):
                shop_info['is_chain'] = 1
        else: shop_info['name'] = shop_info.get('name_list_page', 'N/A'); shop_info['is_chain'] = 0

        rating_tag = detail_soup.select_one('div.star-score.wx-view, .brief-info .mid-score .star, .overview-main-item .star-score, .rank-info .star, .shop-comment-score .star')
        if rating_tag:
            rating_text = rating_tag.get('title', '') or rating_tag.get_text(strip=True)
            shop_info['rating'] = extract_first_number(rating_text.replace("星","").replace("分","")) if extract_first_number(rating_text.replace("星","").replace("分","")) is not None else 'N/A'
        else: shop_info['rating'] = 'N/A'

        sub_score_selectors = ["div.topInfo div.rightPanel div.bottomPanel span.scoreText.wx-text", "span.scoreText.wx-text:-soup-contains('口味')", "div.brief-info .item.score", ".comment-rst .stars", "div.shopAvgScore", ".shop-comment-score span.item"]
        sub_score_text = 'N/A'; sub_score_element_found = False
        for selector in sub_score_selectors:
            elements = detail_soup.select(selector); temp_text = ""
            for el in elements: temp_text += el.get_text(strip=True) + " "
            if '口味' in temp_text or '环境' in temp_text or '服务' in temp_text: sub_score_text = temp_text.strip(); sub_score_element_found = True; break
        if sub_score_element_found: shop_info['sub_scores'] = parse_sub_scores(sub_score_text)
        else: shop_info['sub_scores'] = {'口味': None, '环境': None, '服务': None}

        addr_tag = detail_soup.select_one("span.addressText, span[itemprop='streetAddress'], div.shop-addr, #address, .address, .address-info .value")
        shop_info["address"] = addr_tag.get_text(strip=True).replace("地址：","").strip() if addr_tag else "N/A"

        map_element = detail_soup.select_one("a[data-lat][data-lng], meta[name='location'], .mapview[data-lat][data-lng]")
        if map_element:
            try:
                if map_element.name == 'meta' and 'content' in map_element.attrs:
                    lat_lng_match = re.search(r'coord:([\d.-]+),([\d.-]+)', map_element['content'])
                    if lat_lng_match: shop_info["lat"], shop_info["lng"] = float(lat_lng_match.group(2)), float(lat_lng_match.group(1))
                else: shop_info["lat"], shop_info["lng"] = float(map_element.get("data-lat")), float(map_element.get("data-lng"))
            except: shop_info["lat"] = shop_info["lng"] = None
        else: shop_info["lat"] = shop_info["lng"] = None

        op_hours_text = None; op_hours_selectors = ['p.info-item:-soup-contains("营业时间") span.item-content', 'span.info-name:-soup-contains("营业时间") + span.info-value', '.businessHours .content', '.businessTime .content', 'div.shopExtraInfoItem:-soup-contains("营业时间") .item-content', '.J_item-value.bizTimeArea:-soup-contains("营业时间")', 'span.biz-time', 'div[class*="time"]:-soup-contains("营业时间") .value', '.time:-soup-contains("营业时间")']
        for selector in op_hours_selectors:
            tag = detail_soup.select_one(selector)
            if tag: op_hours_text = tag.get_text(strip=True); break
        if op_hours_text: shop_info['operating_hours'] = op_hours_text.replace("营业时间：","").replace("营业时间","").replace("工作日","").strip()
        else: shop_info['operating_hours'] = 'N/A'

        shop_info['has_group_purchase_套餐'] = 1 if detail_soup.find(string=re.compile(r"团购|优惠套餐|团:")) or detail_soup.select_one(".group-deal, .promo, .tuan-list") else 0

        # --- 评论数据提取 ---
        print(f"   开始提取店铺 {shop_id} 的评论...")
        shop_info['reviews_data'] = [] # 初始化为空列表
        review_elements = detail_soup.select('div.reviewDetail.wx-view, div.comment-item, .review-item') # 尝试多个评论项选择器

        reviews_scraped_count = 0
        for review_el in review_elements:
            if reviews_scraped_count >= CONFIG["MAX_REVIEWS_TO_SCRAPE_PER_SHOP"]:
                break

            review_data_json_str = review_el.get('data-review')
            review_text_from_html = safe_get_text(review_el, '.reviewText, .review-words') # 直接从HTML提取可见文本

            parsed_review = {}
            if review_data_json_str:
                try:
                    review_json = json.loads(review_data_json_str)
                    parsed_review['user_name'] = review_json.get('userNickName', 'N/A')
                    parsed_review['user_id'] = review_json.get('userId', 'N/A')
                    parsed_review['star_rating'] = review_json.get('star', 0) / 10.0 #  "star":50 -> 5.0
                    parsed_review['add_time'] = review_json.get('lastTimeStr', review_json.get('addTime', 'N/A')) # 优先用 lastTimeStr

                    # 尝试从JSON中提取评论体，如果失败或没有，则用HTML中提取的
                    review_body_from_json = extract_review_text_from_body(review_json.get('reviewBody'))
                    parsed_review['text'] = review_body_from_json if review_body_from_json else review_text_from_html

                except json.JSONDecodeError:
                    print(f"     解析评论JSON失败: {review_data_json_str[:100]}...")
                    parsed_review['text'] = review_text_from_html # 降级使用HTML文本
                except Exception as e_json_parse:
                    print(f"     处理评论JSON时发生其他错误: {e_json_parse}")
                    parsed_review['text'] = review_text_from_html
            else: # 如果没有data-review属性，则只依赖HTML提取
                parsed_review['user_name'] = safe_get_text(review_el, '.userName span.wx-text, .name')
                star_class_el = review_el.select_one('.star-container, .userStar .star') # 查找评分星星容器
                if star_class_el:
                    star_class_text = " ".join(star_class_el.get('class', []))
                    star_match = re.search(r'star_(\d+)', star_class_text) # 例如 star_40
                    if star_match: parsed_review['star_rating'] = int(star_match.group(1)) / 10.0
                parsed_review['add_time'] = safe_get_text(review_el, '.review-lastTime .lastTime-left, .time')
                parsed_review['text'] = review_text_from_html

            if parsed_review.get('text', '').strip(): # 只添加有文本内容的评论
                shop_info['reviews_data'].append(parsed_review)
                reviews_scraped_count += 1

        print(f"   成功提取 {len(shop_info['reviews_data'])} 条评论。")


    except TimeoutException: print(f"错误：等待店铺 {shop_id} 详情页某环节超时。")
    except Exception as e_detail_main: print(f"处理店铺 {shop_id} ({detail_link}) 详情页时发生其他错误: {type(e_detail_main).__name__} - {e_detail_main}")
    finally:
        if driver.current_window_handle != main_window_handle: driver.close()
        driver.switch_to.window(main_window_handle)
        human_sleep(mean=2, min_delay=1, max_delay=3)
    return shop_info

# ==============================================================================
# --- 主执行逻辑 ---
# ==============================================================================
if __name__ == "__main__":
    print("=" * 40); print(f" 大众点评店铺信息爬取脚本 V5.7.4 (评论提取+百度Geocoding+刷新优化)"); print(f" 目标城市ID: {CONFIG['CITY_ID']}, 关键词: {CONFIG['KEYWORD']}"); print(f" 计划爬取页数: 从 {CONFIG['START_PAGE']} 到 {CONFIG['MAX_PAGES_TO_SCRAPE']}"); print("=" * 40)

    cookie_valid = True; driver_path_valid = True
    if "YOUR_DIANPING_COOKIE_STRING_HERE" in CONFIG["DIANPING_COOKIE_STRING"] or not CONFIG["DIANPING_COOKIE_STRING"].strip() or len(CONFIG["DIANPING_COOKIE_STRING"]) < 50:
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 警告 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
        print("! CONFIG 中的 DIANPING_COOKIE_STRING 为空或是占位符。                !");
        print("! 请确保填写真实的、有效的 Cookie 字符串，否则无法登录和抓取。 !");
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"); cookie_valid = False
    if "C:\\path\\to\\your\\chromedriver.exe" in CONFIG["LOCAL_CHROME_DRIVER_PATH"] or \
       "your_actual_path" in CONFIG["LOCAL_CHROME_DRIVER_PATH"] or \
       not CONFIG["LOCAL_CHROME_DRIVER_PATH"]:
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 警告 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
        print("! CONFIG 中的 LOCAL_CHROME_DRIVER_PATH 未配置或为默认占位符。        !");
        print("! 请确保提供正确的 ChromeDriver 路径。                               !");
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"); driver_path_valid = False
    if "YOUR_BAIDU_MAPS_API_KEY_HERE" in CONFIG["BAIDU_MAPS_API_KEY"] or not CONFIG["BAIDU_MAPS_API_KEY"]:
        print("\n警告: BAIDU_MAPS_API_KEY 未配置或为占位符! 地理编码功能将无法使用。")

    if not cookie_valid or not driver_path_valid:
        if input("配置可能存在问题，是否仍要继续 (y/n)? ").lower() != 'y': exit()

    driver = None; all_store_data = []; start_time = time.time()
    try:
        print("正在初始化 WebDriver..."); driver = uc.Chrome(options=chrome_options, driver_executable_path=CONFIG["LOCAL_CHROME_DRIVER_PATH"], patcher_force_close=True, use_subprocess=True, version_main=120) # 根据你的环境可能需要调整 version_main
        print("WebDriver 初始化成功。"); driver.implicitly_wait(10)
        print(f">> 正在注入 Cookie 到域名: {CONFIG['DIANPING_DOMAIN']}")
        inject_cookies(driver, CONFIG["DIANPING_COOKIE_STRING"], CONFIG["DIANPING_DOMAIN"])
        human_sleep(1,0.5,2)
        print(">> 访问大众点评首页...");
        if not safe_get_page(driver, CONFIG["DIANPING_DOMAIN"], max_retry=1, is_list_page=False): print("!! 无法加载大众点评首页。脚本终止。"); exit()
        print("\n*** 请检查浏览器窗口是否已成功登录大众点评。 ***"); print("*** 如果未登录或遇到验证码，请手动操作浏览器完成登录/验证。 ***"); input("*** 完成后，回到此处按 Enter 键继续执行爬虫... ***\n")
        print(">> 应用 Selenium Stealth 设置..."); stealth(driver, languages=["zh-CN", "zh"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"})
        print("Selenium Stealth 设置应用完毕。")

        processed_shop_ids_total = set()
        for current_page_num in range(CONFIG["START_PAGE"], CONFIG["MAX_PAGES_TO_SCRAPE"] + 1):
            print(f"\n======== 正在处理列表第 {current_page_num} 页 ========")
            current_target_url = f"{DIANPING_SEARCH_URL}/p{current_page_num}" if current_page_num > 1 else DIANPING_SEARCH_URL
            print(f"   目标URL: {current_target_url}")
            if not safe_get_page(driver, current_target_url, is_list_page=True): print(f"!! 无法加载列表页 {current_page_num}，尝试跳过。"); human_sleep(10,5,20); continue
            try: WebDriverWait(driver, CONFIG["PAGE_LOAD_TIMEOUT"]).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#shop-all-list ul li, .shop-list li")))
            except TimeoutException:
                print(f"!! 列表页 {current_page_num} 核心内容加载超时。");
                if "verify.meituan.com" in driver.current_url:
                    if not solve_slider_captcha(driver): continue
                    else:
                        if not safe_get_page(driver, current_target_url, is_list_page=True): continue
                elif "404" in driver.title or "找不到页面" in driver.page_source: print("  检测到404或页面不存在，可能已是最后一页。"); break
                else: print("  列表页其他超时问题，跳过此页。"); continue
            random_human_action(driver); human_sleep(1.5,0.8,3)
            search_soup = BeautifulSoup(driver.page_source, 'html.parser')
            shops_on_this_page = parse_dianping_search_list(search_soup, CONFIG["DIANPING_DOMAIN"])
            if not shops_on_this_page and current_page_num > CONFIG["START_PAGE"]: print(f"第 {current_page_num} 页未解析到任何店铺，可能已到末页。");

            shops_processed_this_page = 0
            for shop_base_info in shops_on_this_page:
                if shop_base_info['shop_id'] in processed_shop_ids_total:
                    print(f"店铺 ID: {shop_base_info['shop_id']} ({shop_base_info.get('name_list_page', 'N/A')}) 已处理，跳过。")
                    continue

                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                # --- 修改点：只处理分类为“茶饮果汁”的店铺 ---
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                current_shop_category = shop_base_info.get('category', 'N/A')

                if current_shop_category == target_category:
                    print(f"店铺 ID: {shop_base_info['shop_id']} ({shop_base_info.get('name_list_page', 'N/A')})，分类: '{current_shop_category}'，符合目标，将进入详情页爬取。")
                    time.sleep(random.uniform(1,3))
                    detailed_shop_info = scrape_additional_details(driver, shop_base_info, CONFIG["DIANPING_DOMAIN"], CONFIG["DETAIL_PAGE_CORE_ELEMENT_TIMEOUT"])
                    all_store_data.append(detailed_shop_info)
                    processed_shop_ids_total.add(detailed_shop_info['shop_id'])
                    shops_processed_this_page +=1
                    human_sleep(3.5,2,5.0)
                else:
                    print(f"店铺 ID: {shop_base_info['shop_id']} ({shop_base_info.get('name_list_page', 'N/A')})，分类: '{current_shop_category}'，非 '{target_category}'，跳过详情页爬取。")
                    # 对于不符合分类的店铺，我们不进行任何操作，也不会将其加入 all_store_data

            print(f"本页新增处理 (符合分类 '{target_category}' 的) {shops_processed_this_page} 家店铺。总计已处理 {len(all_store_data)} 家。")
            if current_page_num < CONFIG["MAX_PAGES_TO_SCRAPE"]:
                driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": random.choice(CONFIG["USER_AGENTS"])}); human_sleep(4,2,8)
    except KeyboardInterrupt: print("\n脚本被用户中断。正在尝试保存...")
    except Exception as e_main: print(f"\n主流程中发生严重错误: {type(e_main).__name__} - {e_main}"); import traceback; traceback.print_exc()
    finally:
        if driver:
            print("正在关闭 WebDriver...")
            try:
                driver.quit()
                print("WebDriver 已关闭。")
            except Exception as e_quit:
                print(f"关闭WebDriver时发生错误(可能句柄已失效): {e_quit}")

    # --- 地理编码缺失的地址 ---
    baidu_api_key = CONFIG["BAIDU_MAPS_API_KEY"]
    if all_store_data and baidu_api_key and "YOUR_BAIDU_MAPS_API_KEY_HERE" not in baidu_api_key:
        print("\n--- 开始对缺失经纬度的地址进行地理编码 (使用百度地图API) ---")
        geocoded_count = 0
        for shop_data in all_store_data: # all_store_data 现在只包含符合分类的店铺
            current_address = shop_data.get('address')
            if (shop_data.get('lat') is None or shop_data.get('lng') is None) and \
               current_address and current_address != 'N/A':
                lng, lat = geocode_address_baidu(current_address, baidu_api_key)
                if lng is not None and lat is not None:
                    shop_data['lng'] = lng
                    shop_data['lat'] = lat
                    geocoded_count += 1
                time.sleep(CONFIG["GEOCODING_REQUEST_DELAY"])
        print(f"地理编码完成，共更新了 {geocoded_count} 个店铺的经纬度。")
    else:
        if not all_store_data: print("\n没有抓取到符合目标分类的店铺数据，跳过地理编码。")
        elif not baidu_api_key or "YOUR_BAIDU_MAPS_API_KEY_HERE" in baidu_api_key:
            print("\n未正确配置百度地图API Key (BAIDU_MAPS_API_KEY)，跳过地理编码步骤。")
            print("请在CONFIG中填入有效的百度地图开发者AK。")

    # --- 输出和保存结果 ---
    end_time = time.time()
    print("\n" + "=" * 30)
    if all_store_data: # all_store_data 现在只包含符合分类的店铺
        print(f"爬取结束，总共获取到 {len(all_store_data)} 家符合目标分类 '{target_category}' 的店铺信息。")

        # 将评论数据转换为字符串以便存入CSV
        for shop_item in all_store_data:
            reviews_summary_list = []
            if 'reviews_data' in shop_item and shop_item['reviews_data']:
                for idx, review in enumerate(shop_item['reviews_data']):
                    # 格式化单条评论的摘要
                    review_summary = f"评论{idx+1}: [用户: {review.get('user_name','N/A')}, 评分: {review.get('star_rating','N/A')}, 时间: {review.get('add_time','N/A')}] {review.get('text','').strip()[:100]}" # 截断评论文本
                    reviews_summary_list.append(review_summary)
            # 用换行符连接多条评论摘要
            shop_item['评论摘要'] = " ||| ".join(reviews_summary_list) if reviews_summary_list else "N/A"
            if 'reviews_data' in shop_item: del shop_item['reviews_data'] # 移除原始列表，避免存入CSV问题

        df = pd.DataFrame(all_store_data)
        rename_mapping = {'name': '店铺名称', 'rating': '评分', 'review_count': '评价数量', 'avg_price': '人均价格', 'region': '区域', 'category': '分类', 'operating_hours': '营业时间', 'address': '详细地址', 'lat': '纬度', 'lng': '经度', 'recommended_dishes': '推荐菜', 'is_chain': '是否连锁_1是0否', 'has_group_purchase_套餐': '有无团购套餐_1是0否'}
        df = df.rename(columns=rename_mapping)

        if 'sub_scores' in df.columns:
            try:
                df['sub_scores'] = df['sub_scores'].apply(lambda x: x if isinstance(x, dict) else {'口味': None, '环境': None, '服务': None})
                sub_scores_df = df['sub_scores'].apply(pd.Series).rename(columns={'口味': '口味评分', '环境': '环境评分', '服务': '服务评分'})
                for col_name_to_drop in ['口味评分', '环境评分', '服务评分']:
                    if col_name_to_drop in df.columns: df = df.drop(columns=[col_name_to_drop])
                df = pd.concat([df.drop(columns=['sub_scores'], errors='ignore'), sub_scores_df], axis=1)
            except Exception as e_ss:
                print(f"拆分 sub_scores 时出错: {e_ss}")
                for col_name in ['口味评分', '环境评分', '服务评分']:
                    if col_name not in df.columns: df[col_name] = None
        else: df['口味评分'], df['环境评分'], df['服务评分'] = None, None, None

        final_columns_order = [
            '店铺名称', '是否连锁_1是0否', '有无团购套餐_1是0否', '评分', '评价数量', '人均价格',
            '口味评分', '环境评分', '服务评分', '区域', '分类', '详细地址', '纬度', '经度',
            '营业时间', '推荐菜', '评论摘要', # 新增评论摘要列
            'shop_id', 'link', 'name_list_page'
        ]
        for col in final_columns_order:
            if col not in df.columns: df[col] = None # 确保列存在
        df_final = df[final_columns_order]

        print("\n最终数据（前2行）预览:"); [pprint.pprint(row.to_dict()) for i, row in df_final.head(2).iterrows()]
        try:
            output_filename = f"上海大众点评_{CONFIG['KEYWORD']}_店铺数据_从{CONFIG['START_PAGE']}页到{CONFIG['MAX_PAGES_TO_SCRAPE']}页_分类_{target_category}_geocoded_reviews.csv" # 修改输出文件名以反映分类筛选
            df_final.to_csv(output_filename, index=False, encoding='utf-8-sig')
            print(f"\n数据已成功保存到文件: {output_filename}")
        except Exception as e_csv: print(f"\n保存到CSV文件时出错: {e_csv}")
    else: print(f"未能成功提取到任何分类为 '{target_category}' 的店铺的详细信息。") # 修改提示信息
    total_time = end_time - start_time; print(f"总耗时: {total_time:.2f} 秒 ({total_time/60:.2f} 分钟)。")
    print("=" * 30 + " 脚本执行完毕 " + "=" * 30)