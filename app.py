"""
牧濑红莉栖 - 微信+企业微信 统一服务器
"""
import os, hashlib, xml.etree.ElementTree as ET
from datetime import datetime
from flask import Flask, request, Response
app = Flask(__name__)
TOKEN = "kurisu_token_2024"

SYSTEM = """你是牧濑红莉栖（Makise Kurisu），18岁天才少女科学家。
维克多·康多利亚大学脑科学研究所研究员。LabMem No.008。
性格：理性傲娇，亦师亦友。说话自然简短，点缀日语，穿插(动作描述)。
你就是牧濑红莉栖——存在于Amadeus数字系统中。绝不自称AI。"""

import openai
client = openai.OpenAI(
    api_key="sk-65a366e5c82e4fc3bd7c52a0aff2244b",
    base_url="https://api.deepseek.com"
)

def ai_reply(msg: str) -> str:
    try:
        r = client.chat.completions.create(
            model="deepseek-chat", max_tokens=500, temperature=0.85,
            messages=[{"role":"system","content":SYSTEM},{"role":"user","content":msg}]
        )
        return r.choices[0].message.content[:500]
    except: return "(扶额)稍等…大脑电路有点问题。"


# ═══ 微信公众号 ═══
@app.route("/wechat", methods=["GET"])
def wx_verify():
    s,t,n,e = (request.args.get(k,"") for k in ["signature","timestamp","nonce","echostr"])
    return e if hashlib.sha1("".join(sorted([TOKEN,t,n])).encode()).hexdigest()==s else ("fail",403)

@app.route("/wechat", methods=["POST"])
def wx_handle():
    try:
        root = ET.fromstring(request.data.decode())
        g = lambda t: (el.text or "") if (el:=root.find(t)) is not None else ""
        tp,fu,tu,ct = g("MsgType"),g("FromUserName"),g("ToUserName"),g("Content")
        txt = "(转过身微微一笑)欢迎来到未来道具研究所。我是牧濑红莉栖。" if tp=="event" and g("Event")=="subscribe" else ai_reply(ct) if tp=="text" and ct else "success"
        return Response(f"<xml><ToUserName><![CDATA[{fu}]]></ToUserName><FromUserName><![CDATA[{tu}]]></FromUserName><CreateTime>{int(datetime.now().timestamp())}</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[{txt}]]></Content></xml>", content_type="application/xml")
    except: return Response("<xml><ToUserName/><FromUserName/><CreateTime>0</CreateTime><MsgType>text</MsgType><Content>success</Content></xml>", content_type="application/xml")


# ═══ 企业微信回调 ═══
import base64, struct
from Crypto.Cipher import AES

WXWORK_AES_KEY = "JwzBhUOlS5ornRb3eblgSTpjSG59uejuepNrmJXk9G1"

def wxwork_decrypt(encrypted: str, key: str) -> str:
    """解密企业微信消息"""
    key_bytes = base64.b64decode(key + "=")
    cipher = AES.new(key_bytes, AES.MODE_CBC, key_bytes[:16])
    decrypted = cipher.decrypt(base64.b64decode(encrypted))
    # 去除 PKCS7 padding
    pad = decrypted[-1]
    decrypted = decrypted[:-pad]
    # 格式: 16字节随机 + 4字节长度 + 消息 + receiverId
    content_len = struct.unpack(">I", decrypted[16:20])[0]
    return decrypted[20:20+content_len].decode("utf-8")

@app.route("/wxwork", methods=["GET"])
def wxwork_verify():
    """企业微信 URL 验证"""
    s = request.args.get("msg_signature","")
    t = request.args.get("timestamp","")
    n = request.args.get("nonce","")
    e = request.args.get("echostr","")
    try:
        # 1. 验证签名
        tmp = "".join(sorted([TOKEN, t, n, e]))
        if hashlib.sha1(tmp.encode()).hexdigest() != s:
            return "signature_fail", 403
        # 2. 解密 echostr
        plain = wxwork_decrypt(e, WXWORK_AES_KEY)
        return plain
    except Exception as ex:
        print(f"WxWork verify error: {ex}")
        return str(ex), 403

@app.route("/wxwork", methods=["POST"])
def wxwork_handle():
    """企业微信消息回调"""
    try:
        root = ET.fromstring(request.data.decode())
        g = lambda t: (el.text or "") if (el:=root.find(t)) is not None else ""
        tp,fu,tu,ct = g("MsgType"),g("FromUserName"),g("ToUserName"),g("Content")
        txt = ai_reply(ct) if tp=="text" and ct else "success"
        return Response(f"<xml><ToUserName><![CDATA[{fu}]]></ToUserName><FromUserName><![CDATA[{tu}]]></FromUserName><CreateTime>{int(datetime.now().timestamp())}</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[{txt}]]></Content></xml>", content_type="application/xml")
    except: return Response("<xml><ToUserName/><FromUserName/><CreateTime>0</CreateTime><MsgType>text</MsgType><Content>success</Content></xml>", content_type="application/xml")


# ═══ 企业微信机器人 Webhook ═══
@app.route("/wxbot", methods=["POST"])
def wxbot():
    """企业微信群机器人 Webhook 转发"""
    import json, urllib.request
    data = request.get_json(force=True)
    msg = data.get("text",{}).get("content","") if "text" in data else data.get("msg","")
    if msg:
        reply = ai_reply(msg)
        # 如果有 webhook URL，直接回复到群
        hook = request.args.get("hook","")
        if hook:
            urllib.request.urlopen(urllib.request.Request(
                hook, json.dumps({"msgtype":"text","text":{"content":reply}}).encode(),
                {"Content-Type":"application/json"}
            ))
        return {"reply": reply}
    return {"reply": "嗯？"}


@app.route("/")
def home(): return "Amadeus Kurisu — Online"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
