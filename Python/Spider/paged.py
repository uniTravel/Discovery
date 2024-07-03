import requests
import asyncio
import aiohttp
import pandas as pd

from enum import Enum
from typing import Callable


class Method(Enum):
    Get = 'GET'
    Post = 'POST'
    Put = 'PUT'
    Patch = 'PATCH'


class Mode(Enum):
    Params = 'params'
    Data = 'data'
    Json = 'json'


class Paged:
    """分页方式获取DataFrame
    """

    def __init__(self,
                 url: str,
                 method: Method,
                 mode: Mode,
                 payload: dict,
                 key: str,
                 *,
                 limit: int = 100,
                 headers: dict = {
                     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.38"},
                 proxies: dict | None = None) -> None:
        """构造函数

        :param url: 目标网站
        :param method: 请求的方法，Get、Post、Put、Patch
        :param mode: _descr传入参数的模式，Params、Data、Json
        :param payload: 传入的参数字典
        :param key: 页码的键
        :param limit: 限制异步并发请求的数量，缺省为100
        :param headers: 请求的标头，通常用缺省值即可
        :param proxies: 代理IP，需要通过代理IP反爬时传入
        """
        self.url = url
        self.method = method
        self.mode = mode
        self.payload = payload
        self.key = key
        self.limit = limit
        self.proxies = proxies
        self.args: dict = {'headers': headers, mode.value: payload}

    def locate(self, pageNo: int | None) -> dict:
        """传入页码更新参数字典

        :param pageNo: 页码的值
        :return: 更新后的参数字典
        """
        self.payload[self.key] = pageNo
        return self.args

    def stop(self, f: Callable[[dict], int]) -> int:
        """计算页码范围的终止点

        :param f: 计算终止点的方法
        :return: 页码范围的终止点
        """
        res = requests.request(self.method.value, self.url,
                               proxies=self.proxies, **self.args)
        return f(res.json())

    def get(self, f: Callable[[dict], pd.DataFrame], pageNo: int | None = None) -> pd.DataFrame:
        """同步方式获取单页DataFrame

        :param f: 网站响应的json串提取DataFrame的方法
        :param pageNo: 页码，未传入页码通常获取第一页
        :return: 获取的DataFrame
        """
        res = requests.request(self.method.value, self.url,
                               proxies=self.proxies, **self.locate(pageNo))
        return f(res.json())

    def fetch(self, f: Callable[[dict], pd.DataFrame], range: range) -> pd.DataFrame:
        """同步方式获取指定页码范围的DataFrame

        :param f: 网站响应的json串提取DataFrame的方法
        :param range: 页码范围
        :return: 指定页码范围的DataFrame
        """
        def sget(s: requests.Session, f: Callable[[dict], pd.DataFrame], pageNo: int) -> pd.DataFrame:
            res = s.request(self.method.value, self.url,
                            proxies=self.proxies, **self.locate(pageNo))
            return f(res.json())
        s = requests.Session()
        dfs = [sget(s, f, i) for i in range]
        return pd.concat(dfs)

    async def afetch(self, f: Callable[[dict], pd.DataFrame], range: range) -> pd.DataFrame:
        """异步方式获取指定页码范围的DataFrame

        :param f: 网站响应的json串提取DataFrame的方法
        :param range: 页码范围
        :return: 指定页码范围的DataFrame
        """
        async def aget(client: aiohttp.client.ClientSession, f: Callable[[dict], pd.DataFrame], pageNo: int) -> pd.DataFrame:
            async with client.request(self.method.value, self.url, **self.locate(pageNo)) as res:
                df = f(await res.json())
            return df
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=self.limit)) as client:
            tasks = [asyncio.create_task(aget(client, f, i)) for i in range]
            dfs = await asyncio.gather(*tasks)
        return pd.concat(dfs)
