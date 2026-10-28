from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

options = Options()
options.add_argument("--headless")
driver = webdriver.Edge(options=options)

driver.get("https://moligod.com/trade/")

# 等待页面出现至少一个“最新价格”的文本
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '最新价格')]"))
    )
    print("✅ 页面数据加载完成")
except Exception as e:
    print(f"⚠️ 等待超时: {e}")
    print("继续保存当前页面...")

html = driver.page_source
driver.quit()

with open("output_full.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ 已保存 HTML，文件大小: {len(html)} 字节")