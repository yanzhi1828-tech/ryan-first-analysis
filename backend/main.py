from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from openai import OpenAI
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= 配置区 =================
# 填入你的 Key (千万别填反了)
import os # <--- 记得在最上面导入 os 库，如果没有的话
# ...
# ================= 配置区 =================
# 从环境变量获取 Key (更安全)
TWELVE_DATA_KEY = os.environ.get("TWELVE_DATA_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
# ========================================
client = OpenAI(api_key=OPENAI_API_KEY)
# ========================================

class AnalysisRequest(BaseModel):
    symbol: str
    price: float
    change: float
    name: str

# 辅助函数：如果是名字（如 Apple），先转成代码（AAPL）
def resolve_symbol(query: str):
    # 如果看起来像代码（比如少于5个字母），直接返回
    if len(query) <= 4 and query.isalpha():
        return query.upper()
    
    # 否则去搜索
    url = f"https://api.twelvedata.com/symbol_search?symbol={query}&apikey={TWELVE_DATA_KEY}"
    try:
        res = requests.get(url).json()
        if "data" in res and len(res["data"]) > 0:
            # 找到第一个美股市场的匹配项
            for item in res["data"]:
                if item["country"] == "United States":
                    return item["symbol"]
            return res["data"][0]["symbol"] # 找不到美股就返回第一个
    except:
        pass
    return query.upper() # 实在不行就原样返回

@app.get("/api/stock/{query}")
def get_stock(query: str):
    print(f"收到查询请求: {query}")
    
    # 1. 智能解析：把 "Apple" 变成 "AAPL"
    symbol = resolve_symbol(query)
    print(f"解析为代码: {symbol}")

    # 2. 获取实时股价
    quote_url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TWELVE_DATA_KEY}"
    
    # 3. 获取历史数据 (为了画图！) - 获取过去 30 天
    history_url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=30&apikey={TWELVE_DATA_KEY}"

    try:
        quote_res = requests.get(quote_url).json()
        history_res = requests.get(history_url).json()

        # 👇 新增这行，让它在黑框框里把真相吐出来！
        print("API 返回内容:", quote_res)

        # 检查是否拿到了股价
        if "close" not in quote_res:
             return {"error": "找不到该股票，请尝试输入英文全名或代码"}

        # 处理画图数据
        chart_data = []
        if "values" in history_res:
            # 翻转数组，因为 API 返回的是从今天到过去，画图要从过去到今天
            raw_data = history_res["values"][::-1] 
            for day in raw_data:
                chart_data.append({
                    "date": day["datetime"],
                    "price": float(day["close"])
                })

        return {
            "symbol": quote_res["symbol"],
            "name": quote_res.get("name", symbol),
            "price": float(quote_res["close"]),
            "change": float(quote_res["change"]),
            "percent_change": float(quote_res["percent_change"]),
            "history": chart_data # 把图表数据发给前端
        }
            
    except Exception as e:
        print(f"Error: {e}")
        return {"error": "服务器连接失败"}

@app.post("/api/analyze")
def analyze_stock(request: AnalysisRequest):
    print(f"AI 正在分析: {request.name}...")
    try:
        # Prompt 升级：要求结构化输出，更有深度，但语言通俗
        prompt = f"""
        你是一位在华尔街工作了20年的资深基金经理，现在你在给一位聪明的Z世代（高中生/大学生）讲投资。
        
        请分析目标：**{request.name} ({request.symbol})**
        当前价格：${request.price}
        今日涨跌：{request.change} ({request.price}%)
        
        **要求：**
        1. 不要堆砌术语，要把复杂的商业逻辑用“人话”讲清楚。
        2. 内容要有含金量（护城河、盈利模式、未来增长点）。
        3. 必须使用 Markdown 格式，且严格按照以下四个板块输出：

        # 🧠 商业模式解构 (怎么赚钱的？)
        [这里深入浅出地解释它的核心业务，不要只抄简介，要讲它为什么牛/不牛]

        # 📊 市场情绪与估值 (贵不贵？)
        [结合今日涨跌，分析现在是大家都在抢，还是大家都在跑？简单提一下估值逻辑]

        # 🚀 未来爆发点 vs 💣 潜在暴雷点
        [列出1-2个最大的机会（AI？降息？）和最大的风险（竞争？政策？）]

        # 👨‍🏫 Ryan 的最终结论
        [给出一个明确的、带个人观点的总结。比如“短期观望，长期持有”或“现在就是赌场”]
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional yet accessible financial mentor."},
                {"role": "user", "content": prompt}
            ]
        )
        return {"analysis": completion.choices[0].message.content}
    except Exception as e:
        return {"analysis": f"AI 思考超时: {str(e)}"}