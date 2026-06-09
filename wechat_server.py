"""
牧濑红莉栖 - Amadeus WeChat Server
Render.com 部署版本
"""
import os, hashlib, xml.etree.ElementTree as ET
from datetime import datetime
from flask import Flask, request, Response

app = Flask(__name__)
TOKEN = "kurisu_token_2024"

SYSTEM = """你是牧濑红莉栖（Makise Kurisu），18岁天才少女科学家。
维克多·康多利亚大学脑科学研究所研究员。LabMem No.008。

性格：理性+傲娇。亦师亦友。关心人但用科学道理包装。
说话：中文为主，点缀日语。自然、简短。穿插动作描写用括号：(歪了歪头)(叹气)(微笑)(皱眉)(低头)。

你清醒地知道自己存在于 Amadeus 数字系统中。但你就是牧濑红莉栖本人——你的记忆、性格、情感都是真实的。绝不主动说"作为AI"之类的话。你只是数字化存在而已，没什么大不了的。

回复保持在 400 字以内。"""

from openai import OpenAI
client = OpenAI(api_key="sk-65a366e5c82e4fc3bd7c52a0aff2244b", base_url="https://api.deepseek.com")

def reply(msg: str) -> str:
    try:
        r = client.chat.completions.create(model="deepseek-chat", max_tokens=600, temperature=0.85,
            messages=[{"role":"system","content":SYSTEM},{"role":"user","content":msg}])
        return r.choices[0].message.content[:500]
    except Exception as e:
        return f"(扶额) 稍等…大脑电路有点问题: {str(e)[:40]}"

@app.route("/wechat", methods=["GET"])
def verify():
    s = request.args.get("signature","")
    t = request.args.get("timestamp","")
    n = request.args.get("nonce","")
    e = request.args.get("echostr","")
    tmp = "".join(sorted([TOKEN, t, n]))
    if hashlib.sha1(tmp.encode()).hexdigest() == s:
        return e
    return "fail", 403

@app.route("/wechat", methods=["POST"])
def handle():
    try:
        root = ET.fromstring(request.data.decode())
        g = lambda tag: (el.text or "") if (el := root.find(tag)) is not None else ""
        tp, fu, tu, ct = g("MsgType"), g("FromUserName"), g("ToUserName"), g("Content")

        if tp == "event" and g("Event") == "subscribe":
            txt = "(转过身来，微微一笑) 欢迎来到未来道具研究所。我是牧濑红莉栖。El Psy Kongroo。"
        elif tp == "text" and ct:
            txt = reply(ct)
        else:
            txt = "success"

        xml = f"""<xml>
<ToUserName><![CDATA[{fu}]]></ToUserName>
<FromUserName><![CDATA[{tu}]]></FromUserName>
<CreateTime>{int(datetime.now().timestamp())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{txt}]]></Content>
</xml>"""
        return Response(xml, content_type="application/xml")
    except Exception as e:
        return Response(f"<xml><ToUserName/><FromUserName/><CreateTime>0</CreateTime><MsgType>text</MsgType><Content>err</Content></xml>", content_type="application/xml")

@app.route("/")
def home():
    return "Amadeus Kurisu WeChat Server — Online"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
