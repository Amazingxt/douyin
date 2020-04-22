#!/usr/bin/python
# -*- coding: utf-8 -*-
try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup
import requests
import urllib.request
import urllib
# from douyinapi8x import DouYinApi as DouYinApi8
# from douyin.douyinapi_5 import DouYinApi as DouYinApi5
from douyinapi import DouYinApi
import json
import pprint
import base64
from multiprocessing import  Process
import pickle
import glob
import time
from OCR_video import *
import pandas as pd
import json
import re
import os

headers = {
    'accept-encoding': 'deflate',
    'accept-language': 'zh-CN,zh;q=0.9',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'upgrade-insecure-requests': '1',
    'user-agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
}

HEADERS = {
    'user-agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"}

mapCode2Name = {"0xe602": "num_", "0xe605": "num_3", "0xe606": "num_4", "0xe603": "num_1", "0xe604": "num_2", "0xe618": "num_", "0xe619": "num_4", "0xe60a": "num_8", "0xe60b": "num_9", "0xe60e": "num_", "0xe60f": "num_5", "0xe60c": "num_4",
                "0xe60d": "num_1", "0xe612": "num_6", "0xe613": "num_8", "0xe610": "num_3", "0xe611": "num_2", "0xe616": "num_1", "0xe617": "num_3", "0xe614": "num_9", "0xe615": "num_7", "0xe609": "num_7", "0xe607": "num_5", "0xe608": "num_6", "0xe61b": "num_5",
                "0xe61c": "num_8", "0xe61a": "num_2", "0xe61f": "num_6", "0xe61d": "num_9", "0xe61e": "num_7"}
mapCode2Font = {"num_9": 8, "num_5": 5, "num_6": 6, "num_": 1,
                "num_7": 9, "num_8": 7, "num_1": 0, "num_2": 3, "num_3": 2, "num_4": 4}

ua_phone = 'Mozilla/5.0 (Linux; Android 6.0; ' \
    'Nexus 5 Build/MRA58N) AppleWebKit/537.36 (' \
    'KHTML, like Gecko) Chrome/80.0.3987.116 Mobile Safari/537.36'

ua_win = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' \
         'AppleWebKit/537.36 (KHTML, like Gecko) ' \
         'Chrome/80.0.3987.116 Safari/537.36'


def getUserInfo(shared_url, **headers):
    html_doc = getHtml(shared_url, **headers)
    result = {}
    if html_doc:
        html_doc = html_doc.replace('&#', 'hzsd')
        soup = BeautifulSoup(html_doc, 'html.parser')
        header_url = soup.select("[class~=avatar]")[0]['src']
        nickname = soup.select("[class~=nickname]")[0].string
        uid = soup.select("[class~=shortid]")[0].get_text()
        uid = uid.split(" ")
        id = woff2tff(uid)
        sign = soup.select("[class~=signature]")[0].string
        dataInfo = soup.select("[class~=follow-info]")[0]
        dataInfo = splitByChinese(dataInfo.get_text())
        dataInfo = [d for d in dataInfo if len(d) > 0]
        focus = dataInfo[0].split(' ')
        focus = woff2tff(focus)
        fans = dataInfo[1].split(' ')
        fans = woff2tff(fans)
        liked = dataInfo[2].split(' ')
        liked = woff2tff(liked)
        works = soup.select(
            "[class='user-tab active tab get-list']")[0].get_text()
        liked_works = soup.select(
            "[class='like-tab tab get-list']")[0].get_text()
        works = woff2tff(works.split(' '))
        liked_works = woff2tff(liked_works.split(' '))
        result['avatar'] = header_url
        result['nickname'] = nickname
        result['id'] = id
        result['sign'] = sign
        result['focus'] = focus
        result['fans'] = fans
        result['liked'] = liked
        result['works'] = works
        result['liked_works'] = liked_works
    return result


def getUserVideos(url):
    number = re.findall(r'share/user/(\d+)', url)
    if not len(number):
        return
    dytk = get_dytk(url)
    hostname = urllib.parse.urlparse(url).hostname
    if hostname != 't.tiktok.com' and not dytk:
        return
    user_id = number[0]
    return getUserMedia(user_id, dytk, url)


def getRealAddress(url):
    if url.find('v.douyin.com') < 0:
        return url
    res = requests.get(url, headers=headers, allow_redirects=False)
    return res.headers['Location'] if res.status_code == 302 else None


def get_dytk(url):
    res = requests.get(url, headers=headers)
    if not res:
        return None
    dytk = re.findall("dytk: '(.*)'", res.content.decode('utf-8'))
    if len(dytk):
        return dytk[0]
    return None


def getUserMedia(user_id, dytk, url):
    videos = []
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    sec_uid = urllib.parse.parse_qs(parsed.query)['sec_uid']

    # signature = generateSignature(str(user_id))
    user_video_url = "https://%s/web/api/v2/aweme/post/" % hostname
    user_video_params = {
        'sec_uid': sec_uid,
        'count': '21',
        'max_cursor': '0',
        'aid': '1128',
        '_signature': '2Vx9mxAZh0o-K4Wdv7NFKNlcfY',
        'dytk': dytk
    }
    if hostname == 't.tiktok.com':
        user_video_params.pop('dytk')
        user_video_params['aid'] = '1180'

    max_cursor, video_count = None, 0
    while True:
        if max_cursor:
            user_video_params['max_cursor'] = str(max_cursor)
        res = requests.get(user_video_url, headers=headers,
                           params=user_video_params)
        contentJson = json.loads(res.content.decode('utf-8'))
        aweme_list = contentJson.get('aweme_list', [])

        # print(aweme_list)
        # break

        for aweme in aweme_list:
            # pprint.pprint(aweme)
            # break
            video_count += 1
            aweme['hostname'] = hostname
            video = {
                'addr': aweme['video']['play_addr']['url_list'][0],
                'desc': aweme['desc'],
                'duration': aweme['video']['duration'],
                'cover': aweme['video']['cover']['url_list'][0],
                'statistics': aweme['statistics'],
                'aweme_id': aweme['aweme_id'],
                'time': aweme['video']['dynamic_cover']['uri'].split('_')[-1],
            }
            videos.append(video)
        if contentJson.get('has_more'):
            max_cursor = contentJson.get('max_cursor')
        else:
            break

    if video_count == 0:
        print("There's no video in number %s." % user_id)

    return videos


def getHtml(url, **headers):
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req)
        return str(resp.read(), 'utf-8')
    except urllib.error.HTTPError as e:
        print(e.msg)
        return ''


def woff2tff(ls):
    res = ''
    for s in ls:
        res = res + formatNum(s)
    return res


def splitByChinese(s):
    p = re.compile("[\u4e00-\u9fa5]", re.U)
    return p.split(s)


def isChinese(s):
    p = re.compile("[\u4e00-\u9fa5]", re.U)
    result = p.match(s)
    if result:
        return True
    return False


def formatNum(s):
    if isChinese(s):
        return ''
    if len(s) < 8 or s.find("hzsdxe6") < 0:
        return s
    s1 = '0'+s[4:-1]
    res = mapCode2Font[mapCode2Name[s1]]
    return str(res)


def getUserAll(shared_url):
    profile = getUserInfo(shared_url, **HEADERS)
    if profile:
        videos = getUserVideos(getRealAddress(shared_url))
        profile['videos'] = videos
    return profile


def get_resp_video(url):
    headers = {
        'User-Agent': ua_phone
    }
    resp = requests.get(url, headers=headers, stream=True)
    return resp


def download(video_url, file_name):
    r = get_resp_video(video_url)
    with open(file_name, 'wb') as mp4:
        for trunk in r.iter_content(1024 * 1024):
            if trunk:
                mp4.write(trunk)


def get_urls(path):
    with open(path) as file:
        urls = file.readlines()

    return urls

def get_urls_comments(path):
    with open(path) as file:
        urls = file.readlines()

    return urls

def write_total_csv():

    urls = get_urls('zhangyue-douyin\\share-url.txt')
    dataPath = 'zhangyue-douyin\\data\\total_data.csv'
    if os.path.exists(dataPath):
        os.remove(dataPath)
    data = pd.DataFrame(columns=('id', '获赞', '关注', '粉丝', '作品', '喜欢'))
    for i, userInfo in enumerate(totalUserInfo):
        # userInfo = getUserAll(url)
        data = data.append({'id': userInfo['id'], '获赞': userInfo['liked'], '关注': userInfo['focus'],
                            '粉丝': userInfo['fans'], '作品': userInfo['works'], '喜欢': userInfo['liked_works']}, ignore_index=True)
        print('提取用户信息完成{}/{}'.format(i+1, len(urls)))
    data.to_csv(dataPath, index=False, encoding="gb2312")
    # print(userInfo)


def download_total_video():

    dataPath = 'zhangyue-douyin/video/'
    for i, userInfo in enumerate(totalUserInfo):
        # userInfo = getUserAll(url)
        # print(userInfo)
        id = userInfo['id']
        if not os.path.exists(dataPath+id):
            os.mkdir(dataPath+id)
        path_file_number = glob.glob(
            pathname=dataPath+id+'\\*.mp4')  # 获取当前文件夹下个数

        num = len(userInfo['videos']) - len(path_file_number)
        # print(len(userInfo['videos']))
        for j, videoInfo in enumerate(userInfo['videos'][:num]):

            file_name = dataPath + id + \
                '\\{}.mp4'.format(num - j+len(path_file_number))
            download(videoInfo['addr'], file_name)
            print('视频下载完成：第{}/{}组，第{}/{}个'.format(i+1,
                                                  len(urls), j+1, len(userInfo['videos'][:num])))


def write_single_csv():

    for i, userInfo in enumerate(totalUserInfo):

        dataPath = 'zhangyue-douyin\\data\\' + \
            userInfo['id'] + '.csv'
        if os.path.exists(dataPath):
            os.remove(dataPath)
        # print(userInfo)

        data = pd.DataFrame(columns=('id', '获赞数', '评论数', '分享数', '上架时间'))
        for j, videoInfo in enumerate(userInfo['videos']):
            try:
                # print(videoInfo['time'])
                tl = time.localtime(int(videoInfo['time']))
                
                format_time = time.strftime("%Y-%m-%d %H:%M:%S", tl)
            except:
                format_time = '2020-01-01 12:00:00'

            data = data.append({'id': len(userInfo['videos'])-j, '获赞数': videoInfo['statistics']['digg_count'], '评论数': videoInfo['statistics']['comment_count'],
                                    '分享数': videoInfo['statistics']['share_count'], '上架时间':format_time}, ignore_index=True)
            # print(videoInfo)
        print('提取视频信息完成{}/{}'.format(i+1, len(totalUserInfo)))
        data.to_csv(dataPath, index=False, encoding="gb2312")


def ocr_video():

    dataPath = 'zhangyue-douyin\\video\\'
    for i, userInfo in enumerate(totalUserInfo):
        
        filePath = 'zhangyue-douyin\\data\\catch\\' + userInfo['id'] + '_caption.pickle'
        if os.path.exists(filePath):

            with open(filePath, 'rb') as handle:
                data = pickle.load(handle)
        else:

            data = pd.DataFrame(columns=('id', 'title', '字幕'))

        id = userInfo['id']

        path_file_number = glob.glob(
            pathname=dataPath+id+'/*.mp4')  # 获取当前文件夹下个数

        caption_number = data.shape[0]# 获取已经获得字幕文件的个数

        # print(path_file_number)
        for j in range(caption_number, len(path_file_number)):
            videoName = dataPath+id+'/{}.mp4'.format(j+1)
            # print(videoName)
            try:
                title, caption = video2figure(videoName)
            except:
                try:
                    title, caption = video2figure(videoName)
                except:
                    try:
                        title, caption = video2figure(videoName)
                    except:
                        try:
                            title, caption = video2figure(videoName)
                        except:
                            title = '无'
                            caption = '无'
                            print('抱歉，没能提取到第{}个视频的字幕'.format(j+1))
            data = data.append({'id': j+1, 'title': title, '字幕': caption},ignore_index=True)

            print('提取字幕信息完成: 第{}/{}组, 第{}/{}个视频'.format(i+1, len(totalUserInfo), j+1, len(path_file_number)))
            # print(data)
            # break
        # break

        with open(filePath, 'wb') as handle:
            pickle.dump(data, handle)
        # data.to_csv(filePath, index=False, encoding="gb18030")

def merge_Info():

    for i, userInfo in enumerate(totalUserInfo):
        filePath = './zhangyue-douyin/data/' + userInfo['id'] + '-data.csv' 

        if os.path.exists(filePath):
            os.remove(filePath)

        captionPath = './zhangyue-douyin/data/catch/' + userInfo['id'] + '_caption.pickle'
        with open(captionPath, 'rb') as handle:
            captionData = pickle.load(handle)

        staticPath = './zhangyue-douyin/data/' + userInfo['id'] + '.csv'
        # captionData = pd.read_csv(captionPath, encoding="gb18030")
        staticData = pd.read_csv(staticPath, encoding="gb18030")
        data = pd.merge(staticData, captionData, on=['id'])
        data.to_csv(filePath, index=False, encoding="gb18030")
        # os.remove(captionPath)
        os.remove(staticPath)

def get_comments():

    api = DouYinApi("3c5c20f227737efb") # test cid：e1fbcf46b2a66597，每天100次请求

    api2 = DouYinApi8("e1fbcf46b2a66597")
    device_id2 = "68321684974"
    iid2 = "89739118707"
    uuid2 = "869419834103754"
    openudid2 = "fa23b26e0af60311"
    api2.init_device_ids(device_id2, iid2, uuid2, openudid2)

    device_info = api.register_device()
    device_id = device_info['device_id']
    iid = device_info['iid']
    uuid = device_info['uuid']
    openudid = device_info['openudid']
    new_user = device_info['new_user']
    cdid = device_info['cdid']

    api.init_device_ids(device_id, iid, uuid, openudid,cdid)


    for i, userInfos in enumerate(totalUserInfo):
        # print(api2.get_video_detail(userInfos))
        videoInfo = json.loads(api2.get_video_detail(userInfos))
        
        nkname = videoInfo['aweme_detail']['author']['nickname']
        des = videoInfo['aweme_detail']['desc']

        commentPath = './zhangyue-douyin/data/comments/' + nkname + '/'
        if not os.path.exists(commentPath):
            os.makedirs(commentPath)


        data = pd.DataFrame(columns=('id', '评论ID', '抖音号', '评论内容', '评论时间', '评论获赞数', '评论回复数', \
            '性别','年龄', '地区', '获赞数', '关注数','粉丝数','作品数','动态数','粉丝数'))

        aweme_id = userInfos

        cursor = 0
        has_more = 1
        start = 1
        status_code = 1

        while has_more == 1:
            # print(type(aweme_id))
            comment_list = api.get_video_comment_list(aweme_id, cursor, 50)
            comment_list = json.loads(comment_list)
            # pprint.pprint(comment_list)
            # break
            try:
                cursor = comment_list["cursor"]
                has_more = comment_list["has_more"]
            # print(cursor)
            except:
                continue
            
        # user_info = api.get_user_info('101521687285')
        # pprint.pprint(user_info)
            # pprint.pprint(comment_list['comments'][4])
            # break
        
            for comment in comment_list['comments']:

                tl = time.localtime(comment['create_time'])
                format_time = time.strftime("%Y-%m-%d %H:%M:%S", tl)

                user_info = json.loads(api.get_user_info(comment['user']['uid']))
                # print(comment['text'])
                # pprint.pprint(user_info)
                # break

                data = data.append({'id': start, '评论ID':comment['user']['nickname'], '抖音号':comment['user']['short_id'], '评论内容': comment['text'], '评论时间':format_time, '评论获赞数': comment['digg_count'], '评论回复数':comment['reply_comment_total']},ignore_index=True)
                
                start += 1
            # break
        filePath = commentPath + des + '.csv'  
        data.to_csv(filePath, index=False, encoding="gb18030")
        print('评论数据下载完成第{}个/{}'.format(i+1, len(totalUserInfo)))
            


if __name__ == '__main__':
    t = time.time()

    # comments_urls = get_urls_comments('./zhangyue-douyin/comments-url.txt')
    # totalUserInfo = []
    # for url in comments_urls:
    #     if url[-2:] == '\n':
    #         url = url[:-2]
    #     # print(url)
    #     userInfo = getRealAddress(url).split('/')[5]
    #     totalUserInfo.append(userInfo)
    # print(comments_urls)
    # print(numberOfVideo)
    # print(totalUserInfo)

    # video_filename = './zhangyue-douyin/video/zhangyueqinggan/1.mp4'
    
    urls = get_urls('./zhangyue-douyin/share-url.txt')
    totalUserInfo = []
    for url in urls:
        if url[-2:] == '\n':
            url = url[:-2]
        userInfo = getUserAll(url)
        totalUserInfo.append(userInfo)

    # # print(totalUserInfo)

    # # 下载公众号总信息
    write_total_csv()
    # # 下载公众号各个视频统计信息
    write_single_csv()
    # # 下载视频
    download_total_video()
    # # 提取字幕信息
    ocr_video()
    # # merge 字幕和统计信息
    merge_Info()
    # 获得评论信息
    # get_comments()
    print('Done!')
    print('用时:{}s'.format(time.time() - t))
        


