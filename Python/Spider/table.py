import requests
import pandas as pd
from lxml import etree

pd.set_option('display.max_rows', None)

url = "https://www.educity.cn/mpacc/2112742.html"
res = requests.get(url)
elem = etree.HTML(res.text, etree.HTMLParser())
table = elem.xpath('//table')
table = etree.tostring(table[0]).decode()
df = pd.read_html(table, encoding='utf-8', header=0)[0]
df.loc[~(df['学校'] == '学校')]
