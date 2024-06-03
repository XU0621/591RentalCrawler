from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time

def fetch_rental_info(driver, page):
    url = f'https://rent.591.com.tw/?kind=0&region=3&firstRow={page * 30}'
    driver.get(url)
    time.sleep(2)  # 等待页面加载

    # 获取页面源代码并解析
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    rental_info_list = []

    # 使用正确的选择器找到包含房源信息的元素
    houses = soup.find_all('section', class_='vue-list-rent-item')
    print(f"Found {len(houses)} houses on page {page + 1}")

    for house in houses:
        try:
            title_element = house.find('div', class_='item-title')
            area_element = house.find('div', class_='item-area')
            price_element = house.find('div', class_='item-price-text')
            style_element = house.find('ul', class_='item-style')  # 使用 ul 标签定位项目列表
            link_element = house.find('a', class_='item-title')
            data_bind_value = house.get('data-bind')  # 获取 data-bind 属性值

            title = title_element.text.strip() if title_element else "N/A"
            area = area_element.text.strip() if area_element else "N/A"
            price = price_element.text.strip() if price_element else "N/A"

            # 获取 item-style 列表中的每个列表项
            style_items = [item.text.strip() for item in style_element.find_all('li')] if style_element else []

            link = f"https://rent.591.com.tw/{data_bind_value}" if data_bind_value else "N/A"

            info = {
                'title': title,
                'area': area,
                'price': price,
                'styles': style_items,  # 保存为列表
                'link': link
            }
            rental_info_list.append(info)
        except Exception as e:
            print(f"Error extracting house info: {e}")
    
    return rental_info_list

def save_to_csv(rental_info_list):
    # 确定最长的 style 列表长度
    max_style_length = max(len(info.get('styles', [])) for info in rental_info_list)

    # 生成 CSV 列名
    fieldnames = ['title', 'area', 'price'] + [f'style_{i+1}' for i in range(max_style_length)] + ['link']

    # 保存到CSV文件
    with open('rental_info.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for rental_info in rental_info_list:
            # 填充 style 列表，确保长度与 max_style_length 一致
            styles = rental_info.get('styles', []) + [''] * (max_style_length - len(rental_info.get('styles', [])))
            row = {
                'title': rental_info['title'],
                'area': rental_info['area'],
                'price': rental_info['price'],
                'link': rental_info['link'],
                **{f'style_{i+1}': styles[i] for i in range(max_style_length)}
            }
            writer.writerow(row)

def filter_and_reorder_csv():
    with open('rental_info.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        filtered_rows = [row for row in reader if row['style_4'].strip()]

    # 新的列顺序和重命名
    fieldnames = ['title', 'link', 'area', 'style_2', 'style_3', 'style_4', 'price']
    renamed_fieldnames = {
        'title': 'title',
        'link': 'link',
        'area': 'addr',
        'style_2': 'style',
        'style_3': 'size',
        'style_4': 'floor',
        'price': 'price'
    }

    with open('rental_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[renamed_fieldnames[field] for field in fieldnames])
        
        writer.writeheader()
        for row in filtered_rows:
            reordered_row = {renamed_fieldnames[field]: row[field] for field in fieldnames}
            writer.writerow(reordered_row)

def main():
    # 使用 Chrome 浏览器
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    rental_info_list = []

    for page in range(0, 1):  # Adjust range to get more pages if necessary
        info_list = fetch_rental_info(driver, page)
        rental_info_list.extend(info_list)
        time.sleep(1)  # Add delay to avoid being blocked

    driver.quit()

    save_to_csv(rental_info_list)
    filter_and_reorder_csv()

if __name__ == "__main__":
    main()
