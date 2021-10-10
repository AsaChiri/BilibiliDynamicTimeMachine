import requests
import json
import jsonlines
import time
import os
import sys
from retrying import retry
import traceback

class User():
    def __init__(self, uid):
        self.uid = str(uid)

    def get_info(self):
        url = f'https://api.bilibili.com/x/space/acc/info?mid={self.uid}'
        return Get(url)['data']

    def get_dynamic(self, offset):
        # need_top: {1: 带置顶, 0: 不带置顶}
        url = f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={self.uid}&offset_dynamic_id={offset}&need_top=0'
        return Get(url)['data']

    def get_live_info(self):
        url = f'https://api.live.bilibili.com/room/v1/Room/getRoomInfoOld?mid={self.uid}'
        return Get(url)['data']


def Get(url):
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/79.0.3945.130 Safari/537.36",
        "Referer": "https://www.bilibili.com/"
    }
    r = requests.get(url, headers=DEFAULT_HEADERS)
    return r.json()

def checkAndCreate(dirs):
    if not os.path.exists(dirs):
        os.makedirs(dirs)

@retry(wait_random_min=1000, wait_random_max=3000)
def save_file(url, output_dir):
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/79.0.3945.130 Safari/537.36",
        "Referer": "https://www.bilibili.com/"
    }
    response = requests.get(url,headers=DEFAULT_HEADERS,timeout=10)
    img = response.content
    # 保存路径
    filename = url.split("?")[0].split("/")[-1]
    with open(os.path.join(output_dir, filename), 'wb') as f:
        f.write(img)
    print(f"保存 {url} 到文件 {os.path.join(output_dir, filename)}")
    return os.path.join(output_dir, filename)


class DynamicSaver():
    def __init__(self, dynamic,path_dict):
        self.dynamic = dynamic
        self.type = dynamic['desc']['type']
        self.id = dynamic['desc']['dynamic_id']
        self.url = "https://t.bilibili.com/" + str(self.id)
        self.time = dynamic['desc']['timestamp']
        # self.origin_id = dynamic['desc']['orig_dy_id']
        self.name = dynamic['desc']['user_profile']['info']['uname']
        self.uid = dynamic['desc']['user_profile']['info']['uid']
        self.card = json.loads(dynamic['card'])

        self.forwards_file = path_dict['forwards_file']
        self.videos_file = path_dict['videos_file']
        self.short_videos_file = path_dict['short_videos_file']
        self.audios_file = path_dict['audios_file']
        self.dynamics_file = path_dict['dynamics_file']
        self.albums_file = path_dict['albums_file']
        self.articles_file = path_dict['articles_file']
        self.calendars_file = path_dict['calendars_file']

        self.images_dir = path_dict['images_dir']
        self.short_videos_dir = path_dict['short_videos_dir']

    def format(self):
        try:
            if self.type == 1:
                # 转发动态
                msgs = {
                    "dynamic_id": self.id,
                    "time": self.time,
                    "content": self.card['item']['content'],
                    "origin": self.dynamic['desc']['origin']['dynamic_id']
                }
                with jsonlines.open(self.forwards_file, "a") as f:
                    f.write(msgs)
            elif self.type == 2:
                # 相簿
                pictures_urls = [pic['img_src']
                                 for pic in self.card['item']['pictures']]
                pictures_urls_local = [save_file(
                    url, self.images_dir) for url in pictures_urls]
                msgs = {
                    "dynamic_id": self.id,
                    "time": self.time,
                    "content": {
                        "description": self.card['item']['description'],
                        "pictures": pictures_urls,
                        "pictures_local": pictures_urls_local
                    }
                }
                with jsonlines.open(self.albums_file, "a") as f:
                    f.write(msgs)
            elif self.type == 4:
                # 普通动态
                msgs = {
                    "dynamic_id": self.id,
                    "time": self.time,
                    "content": self.card['item']['content']
                }
                with jsonlines.open(self.dynamics_file, "a") as f:
                    f.write(msgs)
            elif self.type == 8:
                # 视频投稿
                msgs = {
                    "dynamic_id": self.id,
                    "time": self.time,
                    "dynamic": self.card['dynamic'],
                    "video": {
                        "bvid": self.dynamic['desc']['bvid'],
                        "title": self.card['title'],
                        "desc": self.card['desc']
                    }
                }
                with jsonlines.open(self.videos_file, "a") as f:
                    f.write(msgs)
            elif self.type == 16:
                # 短视频
                url = self.card['item']['video_playurl']
                local_url = save_file(url, self.short_videos_dir)
                msgs = {
                    "dynamic_id": self.id,
                    "time": self.time,
                    "short_video": {
                        "url": url,
                        "url_local": local_url,
                        "description": self.card['item']['description'],
                    }
                }
                with jsonlines.open(self.short_videos_file, "a") as f:
                    f.write(msgs)
            elif self.type == 64:
                # 专栏
                msgs = {
                    "dynamic_id": self.id,
                    "time": self.time,
                    "article": {
                        "cvid": self.card['id'],
                        "title": self.card['title'],
                        "summary": self.card['summary']
                    }
                }
                with jsonlines.open(self.articles_file, "a") as f:
                    f.write(msgs)
            elif self.type == 256:
                # 音频
                msgs = {
                    "dynamic_id": self.id,
                    "time": self.time,
                    "audio": {
                        "auid": self.card['id'],
                        "title": self.card['title']
                    }
                }
                with jsonlines.open(self.audios_file, "a") as f:
                    f.write(msgs)
            elif self.type == 2048:
                # 直播日历
                msgs = {
                    "dynamic_id": self.id,
                    "time": self.time,
                    "content": self.card['vest']['content']
                }
                with jsonlines.open(self.calendars_file, "a") as f:
                    f.write(msgs)
            else:
                print("未知 ", self.type, self.card)
        except Exception as exc:
            print(str(exc))
            print(self.dynamic)
            traceback.print_exc()



import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Save bilibili dynamic data including all images to local given a specific account.')
    parser.add_argument('uid', type=int, nargs=1,
                        help='UID of the account you want to save its dynamics')
    parser.add_argument('-n', dest='name', type=str,
                        help='The name to use in the local save. If not specified, the username of the bilibili account will be used')
    parser.add_argument('-o', dest='save_root', type=str,
                        help='The root directory of the local save')

    args = parser.parse_args()
    uid = args.uid[0]
    user = User(uid)

    if args.name:
        name = args.name
    else:
        name = user.get_info()['name']
    
    save_root = './'
    if args.save_root:
        save_root = args.save_root
    save_paths = {
        'forwards_file':os.path.join(save_root,f"{name}_forwards.jsonl"),
        'videos_file':os.path.join(save_root,f"{name}_videos.jsonl"),
        'short_videos_file':os.path.join(save_root,f"{name}_short_videos.jsonl"),
        'audios_file':os.path.join(save_root,f"{name}_audios.jsonl"),
        'dynamics_file':os.path.join(save_root,f"{name}_dynamics.jsonl"),
        'albums_file':os.path.join(save_root,f"{name}_albums.jsonl"),
        'articles_file':os.path.join(save_root,f"{name}_articles.jsonl"),
        'calendars_file':os.path.join(save_root,f"{name}_calendar.jsonl"),

        'images_dir':os.path.join(save_root,f"{name}_images"),
        'short_videos_dir':os.path.join(save_root,f"{name}_short_video")
    }
    
    
    checkAndCreate(save_paths['images_dir'])
    checkAndCreate(save_paths['short_videos_dir'])
    offset = 0
    while True:
        dynamics = user.get_dynamic(offset)  # 获取最近十二条动态
        nums = len(dynamics['cards'])
        print("获取动态条数：", nums)
        for d in dynamics['cards']:
            dd = DynamicSaver(d,path_dict=save_paths)
            dd.format()
        if dynamics['has_more'] == 1:
            offset = dynamics['next_offset']
            time.sleep(5)
        else:
            break

