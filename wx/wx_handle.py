import json
import time

import aiohttp
import requests
from flask import jsonify
from flask import request
from loguru import logger
from websockets import headers

import wx.receive as receive  # 接收微信消息的地形
import wx.reply as reply  # 将要答复的信息包装成微信需要的xml格式
from wx.verification import signature as f_signature  # 签名算法


class WxHandle:

    @staticmethod
    def post():
        """
        响应微信的post请求，微信用户发送的信息会使用Post请求
        :return:
        """
        try:
            logger.info("接收微信消息->\n" + str(request.data))
            # 对微信传来的xml信息进行解析，解析成我们自定义的对象信息
            receive_msg = receive.parse_xml(request.data)
            string = receive_msg.content.decode('utf-8')
            logger.info(string)
            # 如果解析成功
            if isinstance(receive_msg, receive.Msg):
                # 该微信信息为文本信息
                if receive_msg.type == "text":
                    # 创建一条文本信息准备返回给微信，文本内容为“测试”
                    # msg = reply.TextMsg(receive_msg, "测试")
                    url = 'http://192.168.3.122:7861/chat/chat'
                    json_data = {
                        'query': string,
                        'conversation_id': '',
                        'history_len': 4,
                        'history': [],
                        'stream': 'false',
                        'model_name': 'chatglm3-6b',
                        'temperature': 0.7,
                        'max_tokens': 200,
                        'prompt_name': 'default'
                    }
                    # 调用目标API
                    try:
                        response = requests.post(url, json=json_data, timeout=60)
                        print("post once!")
                    except requests.exceptions.Timeout:
                        # 请求超过了设定的超时时间
                        print('请求超时，服务器长时间无响应。')
                    except requests.exceptions.RequestException as e:
                        # 网络连接错误或其他请求错误
                        print(f'Request failed: {e}')
                    # 检查响应状态码是否为200（请求成功）
                    if response.status_code == 200:
                        # 这里可以根据需要处理返回的数据
                        # 这里假设数据始终以'data: '开头
                        json_str = response.text.split('data: ', 1)[1]
                        # 解析JSON字符串为Python字典
                        data_dict = json.loads(json_str)
                        # 提取"text"键的值
                        text_value = data_dict.get("text", "")
                        msg = reply.TextMsg(receive_msg, text_value)
                    else:
                        # 如果响应状态码不是200，处理错误情况
                        return jsonify({'error': 'API request failed'}), response.status_code
                    # 发送我创建的文本信息
                    print("message send once!")
                    try:
                        return msg.send()
                    except Exception as e:
                        print(e)
                else:
                    # 该信息不为文本信息时，发送我定义好的一条文本信息给他
                    return reply.Msg(receive_msg).send()
        except Exception as e:
            logger.error("解析微信XML数据失败！")
            logger.error(e)
        return "xml解析出错"

    @staticmethod
    def get():
        """
        响应微信的get请求，微信的验证信息会使用get请求
        这里的验证方式是按照微信公众号文档上的教程来做的
        :return:
        """
        # 微信传来的签名，需要和我生成的签名进行比对
        signature = request.args.get('signature')  # 微信已经加密好的签名，供我比对用
        timestamp = request.args.get('timestamp')  # 这是我需要的加密信息
        nonce = request.args.get('nonce')  # 也是需要的加密信息
        # 判断该请求是否正常，签名是否匹配
        try:
            # 微信传来的签名与我加密的签名进行比对，成功则返回指定数据给微信
            if signature == f_signature(timestamp, nonce):
                # 微信要求比对成功后返回他传来的echost数据给他
                return request.args.get('echostr')
            else:
                return ""
        except Exception:
            logger.error("签名失败！")
        return "签名失败！"
