import json
import random
import time
import uuid
from urllib import parse

import requests


class DouYinApi:

    USER_AGENT = 'com.ss.android.ugc.aweme/960 (Linux; U; Android 5.1.1; zh_CN; 2014813; Build/LMY47V; Cronet/77.0.3844.0)'

    COMMON_DEVICE_PARAMS = {
        'address_book_access': '1',
        'retry_type': 'no_retry',
        'ac': 'wifi',
        'channel': 'aweGW',
        'aid': '1128',
        'app_name': 'aweme',
        'version_code': '960',
        'version_name': '9.6.0',
        'device_platform': 'android',
        'ssmix': 'a',
        'device_type': '2014813',
        'device_brand': 'Xiaomi',
        'language': 'zh',
        'os_api': '22',
        'os_version': '5.1.1',
        'manifest_version_code': '960',
        'resolution': '720*1280',
        'dpi': '320',
        'update_version_code': '9602',
        'app_type': 'normal'
    }

    URL_BASE = "http://47.105.95.219:8080/douyinapi/"

    #PROXY = {'http': 'http://59.63.52.228:32743', 'https': 'http://59.63.52.228:32743'}
    PROXY = {}

    def __init__(self, cid):
        """
        :param cid: client id
        """
        self.__cid = cid
        self.__device_id = ''
        self.__iid = ''
        self.__uuid = ''
        self.__openudid = ''
        self.__device_params = {}
        self.__cookie = {}
        self.__cdid = ''

    def get_api_access_info(self):
        """获取接口使用情况
        :return:
        """
        querys = {
            'cid': self.__cid
        }

        response = requests.get(DouYinApi.URL_BASE + "getApiAccessInfo?" + parse.urlencode(querys))
        return response.text

    def init_device_ids(self, device_id, iid, udid, openudid, cdid):
        """初始化设备id参数
        :param device_id: device id
        :param iid: install id
        :param udid: imei
        :param openudid: open udid
        :param serial_number: serial no
        :param clientudid: client udid
        :param sim_serial_number: sim serial number
        :param mc: mac address
        :return: none
        """
        self.__device_id = device_id
        self.__iid = iid
        self.__uuid = udid
        self.__openudid = openudid
        self.__cdid = cdid
        device_ids = {
            'device_id': device_id,
            'iid': iid,
            'uuid': udid,
            'openudid': openudid,
            'cdid': cdid,
        }
        self.__device_params = self.COMMON_DEVICE_PARAMS.copy()
        self.__device_params.update(device_ids)

    def register_device(self, device_id=None, iid=None, openudid=None, udid=None):
        """获取设备信息，传参数注册老设备，不传参数注册新设备
        :return:
        """
        serial_number = str(uuid.uuid4())[-12:]
        if openudid is None:
            openudid = 'fa23' + str(uuid.uuid4())[-12:]

        clientudid = str(uuid.uuid4())

        if udid is None:
            udid = '869' + self.__get_random(12)
        mc = self.__get_random_mac()
        print(mc)

        if device_id is None:
            device_id = '19' + self.__get_random(9)

        cdid = str(uuid.uuid4())

        dev_params = {
            'serialNumber': serial_number,
            'openudid': openudid,
            'uuid': udid,
            'clientudid': clientudid,
            'deviceId': device_id,
            'mac': mc,
            'cdid': cdid
        }

        dev_params.update(self.COMMON_DEVICE_PARAMS)

        params = {
            'uuid': udid,
            'openudid': openudid,
            '_rticket': str(int(round(time.time() * 1000)))
        }

        params.update(self.COMMON_DEVICE_PARAMS)
        device_register_url = 'https://log.snssdk.com/service/2/device_register/?' + parse.urlencode(params)
        headers = {
            'User-Agent': DouYinApi.USER_AGENT
        }

        resp = requests.post(device_register_url, data=self.get_encrypted_devregister_info(dev_params), headers=headers, proxies=self.PROXY)
        cookie = resp.cookies.get_dict()
        if len(cookie) != 0:
            self.__cookie.update(cookie)
            print('cookie:' + str(self.__cookie))
        resp = resp.json()
        print(resp)
        ids = {
            'device_id': str(resp['device_id']),
            'iid': str(resp['install_id']),
            'uuid': udid,
            'openudid': openudid,
            'serial_number': serial_number,
            'clientudid': clientudid,
            'new_user': resp['new_user'],
            'mc': mc,
            'cdid': cdid
        }
        return ids

    def get_feed(self):
        """获取首页推荐列表
        """
        douyin_url = 'https://aweme-eagle.snssdk.com/aweme/v1/feed/?type=0&max_cursor=0&min_cursor=-1&count=6&volume=0.0&pull_type=2&need_relieve_aweme=0&filter_warn=0&req_from&is_cold_start=0'
        return self.__http_get(douyin_url)

    def get_nearby_feed(self, city_id):
        """获取对应城市的推荐列表
        :param cityid: 城市代码, 从https://wenku.baidu.com/view/af4281bafd0a79563c1e7287.html获取
        :return:
        """
        params = {
            'city': city_id,
        }

        douyin_url = 'https://api.amemv.com/aweme/v1/nearby/feed/?max_cursor=0&min_cursor=0&count=20&feed_style=1&filter_warn=0&poi_class_code=0'
        return self.__http_get(douyin_url, params)

    def get_user_info(self, user_id):
        """获取用户信息
        :param user_id: 用户ID
        :return:
        """
        params = {
            'user_id': user_id
        }

        douyin_url = 'https://aweme-eagle.snssdk.com/aweme/v1/user/?'
        return self.__http_get(douyin_url, params)

    def get_user_post(self, user_id, max_cursor, count):
        """获取用户作品
        :param user_id: 用户ID
        :param max_cursor: 用于分页，第1页是0，后1页是上1页请求的时候返回的max_cursor
        :param count: 返回视频的条数
        :return:
        """
        params = {
            'user_id': user_id,
            'max_cursor': str(max_cursor),
            'count': str(count)
        }

        douyin_url = 'https://aweme.snssdk.com/aweme/v1/aweme/post/'
        return self.__http_get(douyin_url, params)

    def get_user_forward_list(self, user_id, max_cursor, count):
        """获取用户动态
        :param user_id: 用户ID
        :param max_cursor: 用于分页，第1页是0，后1页是上1页请求的时候返回的max_cursor
        :param count: 每次返回的动态条数
        :return:
        """
        params = {
            'user_id': user_id,
            'max_cursor': str(max_cursor),
            'count': str(count)
        }

        douyin_url = 'https://aweme.snssdk.com/aweme/v1/forward/list/'
        return self.__http_get(douyin_url, params)

    def get_user_following_list(self, user_id, max_time, count):
        """获取用户关注列表 注意：关注列表请求太频繁会导致不返回数据
        :param user_id: 用户ID
        :param max_time: 用于分页，第1页是0，后1页是上1页请求时返回的min_time
        :param count: 每次返回的条数
        :return:
        """
        params = {
            'user_id': user_id,
            'max_time': str(int(time.time()) if max_time == 0 else max_time),
            'count': str(count),
            'source_type': '1'
        }

        douyin_url = 'https://aweme.snssdk.com/aweme/v1/user/following/list/'
        return self.__http_get(douyin_url, params)

    def get_user_follower_list(self, user_id, min_time, count):
        """获取用户粉丝列表
        :param user_id: 用户ID
        :param min_time: 用于分页，第1页是0，后1页是上1页请求时返回的min_time
        :param count: 每次返回的条数
        :return:
        """
        params = {
            'user_id': user_id,
            'max_time': str(int(time.time()) if min_time == 0 else min_time),
            'count': str(count)
        }

        douyin_url = 'https://aweme.snssdk.com/aweme/v1/user/follower/list/'
        return self.__http_get(douyin_url, params)

    def get_hot_search_list(self):
        """获取抖音热搜榜
        :return:
        """
        douyin_url = 'https://api.amemv.com/aweme/v1/hot/search/list/?detail_list=1'
        return self.__http_get(douyin_url)

    def get_hot_video_list(self):
        """获取抖音视频榜
        :return:
        """
        douyin_url = 'https://aweme.snssdk.com/aweme/v1/hotsearch/aweme/billboard/'
        return self.__http_get(douyin_url)

    def get_hot_music_list(self):
        """获取抖音音乐榜
        :return:
        """
        douyin_url = 'https://aweme.snssdk.com/aweme/v1/hotsearch/music/billboard/'
        return self.__http_get(douyin_url)

    def get_hot_positive_energy_list(self):
        """获取抖音正能量榜
        :return:
        """
        douyin_url = 'https://aweme.snssdk.com/aweme/v1/hotsearch/positive_energy/billboard/'
        return self.__http_get(douyin_url)

    def get_hot_category_list(self, cursor, count):
        """获取热门分类列表
        :param cursor: 分页用，第1页是0，下一页是上1页请求返回的cursor
        :param count: 每次返回的条数
        :return:
        """
        params = {
            'cursor': str(cursor),
            'count': str(count)
        }

        douyin_url = 'https://aweme.snssdk.com/aweme/v1/category/list/'
        return self.__http_get(douyin_url, params)

    def general_search(self, keyword, offset, count):
        """综合搜索
        :param keyword: 关键词
        :param offset: 分页，第1页是0，下1页是上1页请求返回的cursor
        :param count: 每次返回的条数
        :return:
        """
        params = {
            'keyword': keyword,
            'offset': str(offset),
            'count': str(count),
            'is_pull_refresh': '0',
            'hot_search': '0',
            'latitude': '0.0',
            'longitude': '0.0'
        }

        douyin_url = 'https://aweme-hl.snssdk.com/aweme/v1/general/search/single/?'
        return self.__http_post(douyin_url, params)

    def video_search(self, keyword, offset, count):
        """ 视频搜索
        :param keyword: 关键词
        :param offset: 分页，第1页是0，下1页是上1页请求返回的cursor
        :param count: 每次返回的条数
        :return:
        """
        params = {
            'keyword': keyword,
            'offset': str(offset),
            'count': str(count),
            'is_pull_refresh': '0',
            'hot_search': '0',
            'source': 'video_search'
        }

        douyin_url = 'https://aweme-hl.snssdk.com/aweme/v1/search/item/?'
        return self.__http_post(douyin_url, params)

    def user_search(self, keyword, offset, count):
        """ 用户搜索
        :param keyword: 关键词
        :param offset: 分页，第1页是0，下1页是上1页请求返回的cursor
        :param count: 每次返回的条数
        :return:
        """
        params = {
            'keyword': keyword,
            'cursor': str(offset),
            'count': str(count),
            'type': '1',
            'is_pull_refresh': '0',
            'hot_search': '0',
            'source': ''
        }

        douyin_url = 'https://aweme-hl.snssdk.com/aweme/v1/discover/search/?'
        return self.__http_post(douyin_url, params)

    def get_video_comment_list(self, aweme_id, cursor, count):
        """获取视频评论列表
        :param awemeId: 视频ID
        :param cursor: 分页, 第1页是0, 下1页是上1页请求返回的cursor
        :param count: 每次返回的条数
        :return:
        """
        params = {
            'aweme_id': aweme_id,
            'cursor': str(cursor),
            'count': str(count)
        }

        douyin_url = 'https://aweme.snssdk.com/aweme/v2/comment/list/'
        return self.__http_get(douyin_url, params)

    def get_video_detail(self, aweme_id):
        """获取视频详情
        :param aweme_id: 视频ID
        :return:
        """
        params = {
            'aweme_id': aweme_id
        }

        douyin_url = 'https://aweme.snssdk.com/aweme/v1/aweme/detail/'
        return self.__http_get(douyin_url, params)

    def get_music_detail(self, music_id):
        """获取音乐详情
        :param music_id: 音乐id
        :return:
        """
        params = {
            'music_id': str(music_id),
            'click_reason': '0'
        }

        douyin_url = 'https://aweme.snssdk.com/aweme/v1/music/detail/'
        return self.__http_get(douyin_url, params)

    def get_music_videos(self, music_id, cursor, count):
        """获取音乐对应的视频列表
        :param music_id: 音乐id
        :param cursor: 分页，首页是0，下一页是上一页请求返回的cursor
        :param count: 每次返回的条数
        :return:
        """
        params = {
            'music_id': str(music_id),
            'cursor': str(cursor),
            'count': str(count),
            'type': '6'
        }

        douyin_url = 'https://aweme.snssdk.com/aweme/v1/music/aweme/'
        return self.__http_get(douyin_url, params)

    def get_topic_videos(self, hashtag_name, cursor, count):
        """获取话题相关视频
        :param hashtag_name: 话题
        :param cursor: 分页，首页是0，下一页是上一页请求返回的cursor
        :param count: 每次返回的条数
        :return:
        """
        params = {
            'cursor': str(cursor),
            'count': str(count),
            'source': 'challenge_video',
            'hashtag_name': hashtag_name,
            'type': '5',
            'query_type': '1'
        }

        douyin_url = 'https://aweme-hl.snssdk.com/aweme/v1/challenge/aweme/'
        return self.__http_get(douyin_url, params)

    def get_promotion_list(self, user_id, cursor, count):
        """获取商品橱窗列表
        :param user_id: user id
        :param cursor: 分页，首页是0，下一页是上一页请求返回的cursor
        :param count: 每次返回的条数
        :return:
        """
        params = {
            'count': str(count),
            'cursor': str(cursor),
            'user_id': str(user_id)
        }

        douyin_url = ' https://aweme.snssdk.com/aweme/v1/promotion/user/promotion/list/'
        return self.__http_get(douyin_url, params)

    def get_share_video_detail(self, share_url):
        """获取分享链接对应的视频信息
        :param share_url: 分享链接
        :return:
        """
        headers = {
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
        }

        try:
            resp = requests.get(share_url, headers=headers)
            url_path = parse.urlparse(resp.url).path
            video_id = url_path.split('/')[3]
            return self.get_video_detail(video_id)
        except Exception as e:
            print(repr(e))
        return ''

    def get_webcast_room_info(self, room_id):
        """获取直播房间信息
        :param room_id:
        :return:
        """
        params = {
            'pack_level': '4',
            'room_id': str(room_id),
            'webcast_sdk_version': '1150'
        }

        douyin_url = 'https://webcast.amemv.com/webcast/room/info/?'
        return self.__http_get(douyin_url, params)

    def get_webcast_user_info(self, room_id, user_id):
        """获取直播用户信息
        :param user_id:
        :return:
        """
        params = {
            'request_from': 'admin',
            'current_room_id': str(room_id),
            'target_uid': str(user_id),
            'anchor_id': str(user_id),
            'packed_level': '2',
            'webcast_sdk_version': '1150'
        }

        douyin_url = 'https://webcast.amemv.com/webcast/user/'
        return self.__http_get(douyin_url, params)

    def get_webcast_ranklist(self, room_id, anchor_id):
        """获取直播本场榜
        :param room_id:
        :param anchor_id:
        :return:
        """
        params = {
            'room_id': str(room_id),
            'anchor_id': str(anchor_id),
            'rank_type': '17',
            'webcast_sdk_version': '1150'
        }

        douyin_url = 'https://webcast.amemv.com/webcast/ranklist/room/' + str(room_id) + '/contributor/'
        return self.__http_get(douyin_url, params)

    def encrypt_phone_num(self, phone_num):
        """加密手机号码
        :param phone_num: 手机号码（eg:13501336789）
        :return:
        """
        params = {
            'cid': self.__cid,
            'phone_num': str(phone_num)
        }

        resp = requests.get(DouYinApi.URL_BASE + 'encryptPhoneNum?' + parse.urlencode(params))
        return self.__get_msg(resp)

    def encrypt_param(self, param):
        """加密验证码
        :param param:
        :return:
        """
        params = {
            'cid': self.__cid,
            'param': str(param)
        }

        resp = requests.get(DouYinApi.URL_BASE + 'encryptParam?' + parse.urlencode(params))
        return self.__get_msg(resp)

    def encrypt_xlog(self, xlog):
        """加密xlog
        :param xlog: xlog内容
        :return:
        """
        querys = {
            'cid': self.__cid
        }

        url = DouYinApi.URL_BASE + 'encryptXlog?' + parse.urlencode(querys)
        return requests.post(url, data=xlog, headers={}).content

    def encrypt_tt(self, tt):
        """加密device register info或者app log
        :param tt:
        :return:
        """
        querys = {
            'cid': self.__cid,
            'vc': self.COMMON_DEVICE_PARAMS['version_code']
        }

        url = DouYinApi.URL_BASE + 'encryptTT?' + parse.urlencode(querys)
        return requests.post(url, data=tt, headers={}).content

    def get_encrypted_devregister_info(self, params=None):
        if params is None:
            params = {}

        querys = {
            'cid': self.__cid,
            'vc': self.COMMON_DEVICE_PARAMS['version_code']
        }

        url = DouYinApi.URL_BASE + "getEncryptedDeviceRegInfo?" + parse.urlencode(querys)
        return requests.post(url, data=params, headers={}).content

    def decrypt_xlog(self, xlog):
        """解密xlog
        :param xlog: 加密的xlog内容
        :return:
        """
        querys = {
            'cid': self.__cid
        }

        url = DouYinApi.URL_BASE + 'decryptXlog?' + parse.urlencode(querys)
        return requests.post(url, data=xlog, headers={}).text

    def __get_random(self, len):
        return ''.join(str(random.choice(range(10))) for _ in range(len))

    def __get_msg(self, resp):
        return json.loads(resp.text)['msg']

    def __get_random_mac(self):
        mac = [0x10, 0x2a, 0xb3,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    def __add_common_params(self, douyin_url, params=None):
        if params is None:
            params = {}

        if not douyin_url.__contains__('?'):
            douyin_url = douyin_url + '?'

        common_params = parse.urlencode(self.__device_params)
        if douyin_url.endswith('?') or douyin_url.endswith('&'):
            douyin_url = douyin_url + common_params
        else:
            douyin_url = douyin_url + '&' + common_params

        if len(params) > 0:
            douyin_url = douyin_url + '&' + parse.urlencode(params)
        douyin_url = douyin_url + "&_rticket=" + str(int(round(time.time() * 1000))) + "&ts=" + str(int(time.time()))
        return douyin_url

    def __get_sign_url(self):
        querys = {
            'cid': self.__cid
        }

        sign_url = DouYinApi.URL_BASE + 'getSignature?' + parse.urlencode(querys)
        return sign_url

    def __get_cookie(self):
        if len(self.__cookie) == 0:
            return ''
        return "; ".join([str(x) + "=" + str(y) for x, y in self.__cookie.items()])

    def __get_sign(self, url, headers=None):
        if headers is None:
            headers = {}

        sign_form_params = {
            'url': url,
        }

        sign_form_params.update(headers)
        for i in range(5):
            try:
                sign_resp = requests.post(self.__get_sign_url(), data=sign_form_params).json()
                # print(str(sign_resp))
                if 'ret' in sign_resp:
                    # print(sign_resp)
                    return ""

                if 'xgorgon' not in sign_resp:
                    continue

                if len(sign_resp['xgorgon']) == 0:
                    continue

                sign = {
                    'X-Khronos': sign_resp['xkhronos'],
                    'X-Gorgon': sign_resp['xgorgon'],
                }
                return sign
            except Exception as e:
                print(repr(e))

    def __get_headers(self):
        headers = {
            'User-Agent': DouYinApi.USER_AGENT,
            'X-SS-REQ-TICKET': str(round(time.time() * 1000)),
            'X-SS-DP': '1128',
            'Accept-Encoding': 'gzip, deflate',
            'sdk-version': '1',
            'Cookie': self.__get_cookie()
        }
        return headers

    def __http_get(self, url, query_params=None):
        if query_params is None:
            query_params = {}

        url = self.__add_common_params(url, query_params)
        headers = self.__get_headers()
        sign = self.__get_sign(url, headers)
        headers.update(sign)
        resp = requests.get(url, headers=headers, cookies=self.__cookie, proxies=self.PROXY)
        cookie = resp.cookies.get_dict()
        if len(cookie) != 0:
            self.__cookie.update(cookie)
            print('cookie:' + str(self.__cookie))
        return resp.text

    def __http_post(self, url, form_params=None):
        if form_params is None:
            form_params = {}

        url = self.__add_common_params(url)
        headers = self.__get_headers()
        sign = self.__get_sign(url, headers)
        headers.update(sign)
        resp = requests.post(url, headers=headers, data=form_params, cookies=self.__cookie, proxies=self.PROXY)
        cookie = resp.cookies.get_dict()
        if len(cookie) != 0:
            self.__cookie.update(cookie)
            print('cookie:' + str(self.__cookie))
        return resp.text








