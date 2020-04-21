from aip import AipOcr
import os
from os import path
import base64
import glob
import numpy as np

import difflib

import matplotlib.pyplot as pyplot
from PIL import Image
import cv2


def video2figure(video_filename):

    videoCap = cv2.VideoCapture(video_filename)

    # 帧频
    fps = videoCap.get(cv2.CAP_PROP_FPS)
    # 视频总帧数
    total_frames = int(videoCap.get(cv2.CAP_PROP_FRAME_COUNT))
    # 图像尺寸
    image_size = (
        int(videoCap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        int(videoCap.get(cv2.CAP_PROP_FRAME_WIDTH)),
    )

    # print (image_size)
# 获取文字位置信息，并且提取标题
    for i in range(total_frames):
        sucess, frame = videoCap.read()

        if i  == (15*fps):
            im = frame[:, :, 0]
            # im = im[int(2*image_size[0]/3):3*int(image_size[0]/3), :]
            _, im_arr = cv2.imencode('.jpg', im)
            message = locateOCR(im_arr)
            title_list = message['words_result'][:message['words_result_num']-1]
            title = ','.join([tit['words'] for tit in title_list])

            locate = message['words_result'][-1]['location']
            top = locate['top']
            height = locate['height']
            start = top 
            end = top + height 
            break


# 获取字幕
    videoCap = cv2.VideoCapture(video_filename)
    caption = []
    suspension = []
    preWords = ''
    im_pre = np.zeros([end-start,image_size[1]])
    for i in range(total_frames):
        sucess, frame = videoCap.read()

        if i % int(fps/2) == 0:
            im = frame[:, :, 0]
            im = im[start:end, :]
            # print(np.sum(np.array(im)-im_pre))
            # break
            if np.sum(np.array(im)-im_pre) < 1e5:
                pass
            else:
                _, im_arr = cv2.imencode('.jpg', im)
                message = baiduOCR(im_arr)
                # print(message['words_result'])
                try:
                    for words in message['words_result']:
                        if difflib.SequenceMatcher(None, words['words'], preWords).quick_ratio() < 0.8:
                            caption.append(words['words'])
                            preWords = words['words']
                except:
                    pass

            im_pre = im
    captions = list(set(caption))
    captions.sort(key=caption.index)
    Captions = ','.join(captions)
    # print(','.join(captions))

    #     if i == fps:
    #         im = frame[:, :, 0]
    #         im = im[:int(image_size[0]/3), :]
    #         _, im_arr = cv2.imencode('.jpg', im)
    #         message = baiduOCR(im_arr)
    #         title = [words['words'] for words in message['words_result']]

    #     if i % int(fps) == 0:
    #         im = frame[:, :, 0]
    #         im = im[int(image_size[0]/3):2*int(image_size[0]/3), :]
    #         _, im_arr = cv2.imencode('.jpg', im)
    #         message = baiduOCR(im_arr)
    #         for words in message['words_result']:
    #             suspension.append(words['words'])
    #     suspensions = sorted(list(set(suspension)), key=suspension.index)

    # print(','.join(title), ','.join(captions), ','.join(suspensions))

    return title, Captions


def baiduOCR(img):
    """利用百度api识别文本，并保存提取的文字
    img:    图片
    """

    APP_ID = '19303861'  # 刚才获取的 ID，下同
    API_KEY = 'Gbd6a9l0CvTAL4X8VVyWbAIi'
    SECRECT_KEY = '1SVYUhu3DzYaptryWB3MD5CEMhtWIdas'
    client = AipOcr(APP_ID, API_KEY, SECRECT_KEY)

    message = client.basicGeneral(img)   # 通用文字识别，每天 50 000 次免费
    # message = client.basicAccurate(img)   # 通用文字高精度识别，每天 800 次免费
    # message = client.general(img)

    # 输出文本内容
    return message

def locateOCR(img):
    """利用百度api识别文本，并保存提取的文字
    img:    图片
    """

    APP_ID = '19303861'  # 刚才获取的 ID，下同
    API_KEY = 'Gbd6a9l0CvTAL4X8VVyWbAIi'
    SECRECT_KEY = '1SVYUhu3DzYaptryWB3MD5CEMhtWIdas'
    client = AipOcr(APP_ID, API_KEY, SECRECT_KEY)

    # message = client.basicGeneral(img)   # 通用文字识别，每天 50 000 次免费
    # message = client.basicAccurate(img)   # 通用文字高精度识别，每天 800 次免费
    message = client.general(img) # 通用文字识别（含位置信息）

    # 输出文本内容
    return message


if __name__ == "__main__":
    video_filename = './zhangyue-douyin/video/zhangyueqinggan/95.mp4'
    title, caption = video2figure(video_filename)
    print(title)
    print(caption)
