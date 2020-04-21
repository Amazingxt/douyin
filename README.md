## 使用说明

本项目以抖音中掌阅科技的一系列公众号作为目标，爬取公众号基本信息，下载公众号视频并提取视频的title、字幕和统计信息

##### 目录介绍

/

​	zhangyue-douyin/

​		data/	 * 统计数据文件夹

​		video/	*视频下载文件夹

​		douyin.py	*爬虫主程序

​		share-url.txt	*公众号链接

​		comments-url.txt	*评论视频链接

​		comment.py	*评论爬虫程序

​	config.bat	*设置虚拟环境并下载依赖package

​	requirements.txt	*依赖package

​	run.bat	*主脚本

##### 操作步骤

1、双击运行config.bat，创建python虚拟项目环境并安装依赖，只需要进行一次即可

2、双击运行run.bat，运行爬虫，每次运行爬虫时运行

##### PS说明

1、爬取之前，在 ./zhangyue-douyin/share-url.txt文件内，添加想要爬取的公众号的链接，每行一个（链接获取方法为：点开公众号主页，分享，复制分享链接，复制到微信）

2、爬虫爬取视频信息之前都会检查已经存放的视频并在此基础上爬取，因此如果因为某些原因造成爬取结果不完善，可以将data,video文件夹删除后，重新爬取

