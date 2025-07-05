# backend/main.py

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from engine import run_backtest

# --- 初始化 FastAPI App ---
app = FastAPI()

# --- 配置 CORS 中间件 ---
# 这允许你的前端（未来将在不同端口上运行）访问后端API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Railway部署时会自动配置域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 请求调试中间件
@app.middleware("http")
async def debug_requests(request: Request, call_next):
    print(f"收到请求: {request.method} {request.url}")
    print(f"请求头: {dict(request.headers)}")
    response = await call_next(request)
    print(f"响应状态: {response.status_code}")
    return response

# --- 数据库和工具函数 ---
# 数据库连接配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/dbname')

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def convert_to_yfinance_ticker(stock_code: str, market: str) -> str:
    """根据市场将代码转换为 yfinance 格式"""
    if market == 'A-Share':
        # 检查是否已经包含后缀
        if stock_code.endswith('.SS') or stock_code.endswith('.SZ'):
            return stock_code
        # 如果没有后缀，根据代码添加相应后缀
        return f"{stock_code}.SS" if stock_code.startswith('6') else f"{stock_code}.SZ"
    # 对于美股，代码就是ticker本身
    elif market == 'US':
        return stock_code
    # 可以添加更多市场，如 'HK'
    else:
        return stock_code

# --- API 端点 (Endpoints) ---

@app.get("/")
def read_root():
    return {"message": "欢迎来到投资回测模拟器 API"}

@app.get("/api/health")
def health_check():
    """健康检查端点"""
    return {"status": "ok", "message": "API 正常运行"}

@app.get("/api/routes")
def list_routes():
    """列出所有可用的路由"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })
    return {"routes": routes}

@app.post("/api/test")
async def test_post(data: dict):
    """简单的POST测试端点"""
    print(f"收到测试POST请求: {data}")
    return {"status": "success", "received": data}

@app.get("/api/search")
def search_stocks(q: str = Query(..., min_length=1, description="搜索词，可以是代码或名称")):
    """根据用户输入，从数据库中搜索股票"""
    try:
        conn = get_db_connection()
        if not conn:
            raise Exception("数据库连接失败")
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        search_term = f'%{q}%'
        
        # 搜索股票名称和代码
        cursor.execute(
            "SELECT name, market, yfinance_symbol FROM stocks WHERE name ILIKE %s OR yfinance_symbol ILIKE %s LIMIT 10",
            (search_term, search_term)
        )
        results = cursor.fetchall()
        stocks = [{'name': row['name'], 'market': row['market'], 'code': row['yfinance_symbol']} for row in results]
        
        conn.close()
        
        # 如果没有找到结果，返回一些模拟数据用于测试
        if not stocks:
            test_data = [
                {'name': 'Apple Inc.', 'market': 'US', 'code': 'AAPL'},
                {'name': 'Microsoft Corporation', 'market': 'US', 'code': 'MSFT'},
                {'name': 'Amazon.com Inc.', 'market': 'US', 'code': 'AMZN'},
                {'name': 'Alphabet Inc.', 'market': 'US', 'code': 'GOOGL'},
                {'name': 'Tesla Inc.', 'market': 'US', 'code': 'TSLA'},
                {'name': '贵州茅台', 'market': 'A-Share', 'code': '600519'},
                {'name': '中国平安', 'market': 'A-Share', 'code': '601318'},
            ]
            # 过滤匹配的测试数据
            q_lower = q.lower()
            stocks = [stock for stock in test_data 
                     if q_lower in stock['name'].lower() or q_lower in stock['code'].lower()]
        
        return stocks
        
    except Exception as e:
        print(f"搜索错误: {e}")
        # 如果出现任何错误，返回基本的测试数据
        return [
            {'name': 'Apple Inc.', 'market': 'US', 'code': 'AAPL'},
            {'name': 'Microsoft Corporation', 'market': 'US', 'code': 'MSFT'},
        ]

@app.get("/api/data/{market}/{stock_code}")
def get_stock_data(market: str, stock_code: str, start_date: str, end_date: str):
    """获取指定股票在特定时间范围内的历史数据"""
    ticker = convert_to_yfinance_ticker(stock_code, market)
    
    try:
        # 下载数据，yfinance 会自动处理日期格式
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
        
        if data.empty:
            raise HTTPException(status_code=404, detail="无法获取该股票或该时间段的数据")

        # 处理多层列索引问题
        if isinstance(data.columns, pd.MultiIndex):
            # 展平列索引，只保留第一层（Open, High, Low, Close, Volume）
            data.columns = data.columns.get_level_values(0)
        
        # 将 DataFrame 转换为 JSON 格式返回
        # 重置索引，让日期成为一列，方便前端处理
        data.reset_index(inplace=True)
        return data.to_dict('records')

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据时发生错误: {str(e)}")

class BacktestRequest(BaseModel):
    market: str
    stock_code: str
    start_date: str
    end_date: str
    initial_investment: float = 10000
    monthly_investment: float = 1000

@app.options("/api/backtest")
async def backtest_options():
    """处理CORS预检请求"""
    return {"message": "OK"}

@app.post("/api/backtest")
async def do_backtest(request: BacktestRequest):
    """执行回测并返回结果"""
    print(f"收到回测请求: {request}")  # 调试日志
    
    ticker = convert_to_yfinance_ticker(request.stock_code, request.market)
    print(f"转换后的ticker: {ticker}")  # 调试日志
    
    try:
        # 1. 获取数据
        data = yf.download(ticker, start=request.start_date, end=request.end_date, auto_adjust=True)
        if data.empty:
            raise HTTPException(status_code=404, detail="无法获取数据")

        # 2. 运行回测引擎
        results = run_backtest(data, request.initial_investment, request.monthly_investment)
        
        # 3. 返回结果
        return results

    except ValueError as e:
        print(f"ValueError: {e}")  # 调试日志
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Exception: {e}")  # 调试日志
        raise HTTPException(status_code=500, detail=f"回测过程中发生错误: {str(e)}")

# --- 静态文件服务 ---
# 为前端提供静态文件服务
import os
from fastapi.responses import FileResponse

# 静态文件目录  
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# 首页路由
@app.get("/app")
def read_index():
    """返回前端页面"""
    return FileResponse(os.path.join(static_dir, "index.html"))

# favicon路由
@app.get("/favicon.ico")
def read_favicon():
    """返回favicon"""
    return FileResponse(os.path.join(static_dir, "favicon.ico"))

# 静态资源服务 - 放在最后，避免覆盖API路由
app.mount("/static", StaticFiles(directory=static_dir), name="static")