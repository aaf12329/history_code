from bs4 import BeautifulSoup
import re

with open("output_full.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")


price_labels = soup.find_all("div",class_=(r"bg-ui-surface transition-colors hover:bg-ui-accentSoft"))
print(price_labels)