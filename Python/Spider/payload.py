import json
import requests
import asyncio
import aiohttp
import pandas as pd


url = "https://output.nsfc.gov.cn/baseQuery/data/conclusionQueryResultsData"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.38"
}
cols = ['项目名称', '批准号', '项目类别', '依托单位', '项目负责人', '资助经费', '批准年度', '关键词']
pageSize = 10


def payload(code: str, typ: str, year: str, pageNum: int) -> json:
    """构造请求负载

    :param code: 申请代码
    :param typ: 项目类别代码
    :param year: 结题年度
    :param pageNum: 页码
    :return: 表示请求负载的json串
    """
    return {"ratifyNo": "",
            "projectName": "",
            "personInCharge": "",
            "dependUnit": "",
            "code": code,
            "projectType": typ,
            "subPType": "",
            "psPType": "",
            "keywords": "",
            "ratifyYear": "",
            "conclusionYear": year,
            "beginYear": "",
            "endYear": "",
            "checkDep": "",
            "checkType": "",
            "quickQueryInput": "",
            "adminID": "",
            "pageNum": pageNum,
            "pageSize": pageSize,
            "queryType": "input",
            "complete": "true"}


def total(proxies: json, typ: str, year: str, code: str = 'E07') -> int:
    """获取满足条件的项目总数

    :param proxies: 代理IP，用于突破防爬
    :param typ: 项目类别代码
    :param year: 结题年度
    :param code: 申请代码，缺省为'E07'
    :return: 项目总数
    """
    data = payload(code, typ, year, 0)
    res = requests.post(url, headers=headers, json=data, proxies=proxies)
    return res.json()["data"]['iTotalRecords']


def paged(proxies: json, typ: str, year: str, pageNum: int = 0, code: str = 'E07') -> pd.DataFrame:
    """同步方式分页获取结题项目数据

    :param proxies: 代理IP，用于突破防爬
    :param typ: 项目类别代码
    :param year: 结题年度
    :param pageNum: 页码，缺省为0
    :param code: 申请代码，缺省为'E07'
    :return: 结题项目数据
    """
    data = payload(code, typ, year, pageNum)
    res = requests.post(url, headers=headers, json=data, proxies=proxies)
    df = pd.DataFrame(res.json()["data"]["resultsData"]).iloc[:, 1:9]
    df.columns = cols
    return df


def fetch(proxies: json, typ: str, year: str, code: str = 'E07') -> pd.DataFrame:
    """同步方式获取结题项目数据

    :param proxies: 代理IP，用于突破防爬
    :param typ: 项目类别代码
    :param year: 结题年度
    :param code: 申请代码，缺省为'E07'
    :return: 结题项目数据
    """
    count = int(total(proxies, typ, year)/pageSize+1)
    dfs = [paged(proxies, typ, year, i, code) for i in range(count)]
    return pd.concat(dfs)


async def apaged(client: aiohttp.client.ClientSession, proxy: str, typ: str, year: str, pageNum: int = 0, code: str = 'E07') -> pd.DataFrame:
    """异步方式分页获取结题项目数据

    :param client: 客户端会话
    :param proxy: 代理IP，用于突破防爬
    :param typ: 项目类别代码
    :param year: 结题年度
    :param pageNum: 页码，缺省为0
    :param code: 申请代码，缺省为'E07'
    :return: 结题项目数据
    """
    data = payload(code, typ, year, pageNum)
    async with client.post(url, headers=headers, json=data, proxy=proxy) as res:
        df = pd.DataFrame(res.json()["data"]["resultsData"]).iloc[:, 1:9]
        df.columns = cols
    return df


async def afetch(proxies: json, typ: str, year: str, code: str = 'E07') -> pd.DataFrame:
    """异步方式获取结题项目数据

    :param proxies: 代理IP，用于突破防爬
    :param typ: 项目类别代码
    :param year: 结题年度
    :param code: 申请代码，缺省为'E07'
    :return: 结题项目数据
    """
    count = int(total(proxies, typ, year)/pageSize+1)
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), trust_env=True) as client:
        tasks = [asyncio.create_task(
            apaged(client, proxies['http'], typ, year, i, code)) for i in range(count)]
        dfs = await asyncio.gather(*tasks)
    return pd.concat(dfs)
