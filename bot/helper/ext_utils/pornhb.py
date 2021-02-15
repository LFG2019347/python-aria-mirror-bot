#!/usr/bin/env python
import warnings
warnings.filterwarnings("ignore")
import os
import re
import js2py
import requests
from lxml import etree
import time

headers = {
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66',
    'accept-language':'zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7'
}
proxies = {}
s = requests.Session()

def get_url(url):
    r = s.get(url,headers)
    js= r.json()
    result = list(sorted(js,key=lambda x:int(x.get('quality')),reverse=True))
    return result

def exeJs(js):
    flashvars = re.findall("flashvars_\d+", js)[0]
    js = "\n\t".join(js.split("\n\t")[:-5]).strip()
    js = js.replace("// var nextVideoObject = flashvars_['nextVideo'];",'')
    js+=flashvars
    res = js2py.eval_js(js)
    result_list=[]
    for video in res['mediaDefinitions']:
        video_url = video.get('videoUrl')
        if 'validfrom' in video_url and 'hls' not in video_url:
            result_list.append({'quality':video.get('quality'),'videoUrl':video_url})
        # elif re.search('ttl=\d+&ri=\d+&rs=\d+',video_url):
        #     result_list.append({'quality':video.get('quality'),'videoUrl':video_url})
        elif video.get('remote')==True:
            result = get_url(video_url)
            if result is not None:
                result_list.extend(result)
    if len(result_list)==0:
        return None
    try:
        result_list = list(sorted(result_list,key=lambda x:int(x.get('quality')),reverse=True))
    except Exception as e:
        print(result_list) # 待处理，[480,720]
    return result_list[0]['videoUrl']

def generat_pornhb_url(url,try_num=1):
    url=url.strip()
    resp = s.get(url, headers=headers, proxies=proxies, verify=False)
    html = etree.HTML(resp.content)
    title = "".join(html.xpath("//h1//text()")).strip()
    js_temp = html.xpath("//script/text()")
    for j in js_temp:
        if "flashvars" in j:
            videoUrl = exeJs(j)
            if videoUrl is None:
                continue
            else:
                return videoUrl
    if try_num > 5 and videoUrl is None:
        return url
    else:
        time.sleep(2)
        try_num=try_num+1
        return generat_pornhb_url(url,try_num)

if  __name__=='__main__':
    videoUrl=generat_pornhb_url('https://cn.pornhub.com/view_video.php?viewkey=ph5e6e5bc810a0c')
    print(videoUrl)