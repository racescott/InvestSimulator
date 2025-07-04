# backend/main.py

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from engine import run_backtest, backtest_multiple

# 解决yfinance缓存目录问题
def setup_yfinance():
    """设置yfinance环境，解决部署平台缓存目录问题"""
    try:
        # 1. 创建缓存目录
        cache_dir = os.path.expanduser("~/.cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # 2. 设置用户代理避免被屏蔽
        os.environ['YF_USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        print(f"✅ yfinance环境设置完成，缓存目录: {cache_dir}")
        
    except Exception as e:
        print(f"⚠️ yfinance环境设置失败: {e}")

# 初始化yfinance环境
setup_yfinance()

# 现在安全导入yfinance
import yfinance as yf

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

class StockInfo(BaseModel):
    market: str
    stock_code: str
    name: str

class MultipleBacktestRequest(BaseModel):
    stocks: list[StockInfo]
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
        # 1. 获取数据 - 多重方法和重试机制
        print(f"开始下载 {ticker} 的数据...")
        data = pd.DataFrame()
        
        # 方法1: 标准yf.download
        try:
            data = yf.download(
                ticker, 
                start=request.start_date, 
                end=request.end_date, 
                auto_adjust=True,
                progress=False,
                threads=False  # 避免多线程问题
            )
            print(f"方法1完成，数据行数: {len(data)}")
        except Exception as e:
            print(f"方法1失败: {e}")
        
        # 方法2: 使用Ticker对象 (如果方法1失败)
        if data.empty:
            try:
                print("尝试使用Ticker对象...")
                ticker_obj = yf.Ticker(ticker)
                data = ticker_obj.history(
                    start=request.start_date,
                    end=request.end_date,
                    auto_adjust=True,
                    timeout=30
                )
                print(f"方法2完成，数据行数: {len(data)}")
            except Exception as e:
                print(f"方法2失败: {e}")
        
        # 方法3: 单独获取info然后历史数据 (如果前两种都失败)
        if data.empty:
            try:
                print("尝试分步获取数据...")
                ticker_obj = yf.Ticker(ticker)
                # 先获取基本信息验证ticker有效性
                info = ticker_obj.info
                if info and 'symbol' in info:
                    data = ticker_obj.history(
                        period="1y",  # 改用period而不是日期范围
                        auto_adjust=True
                    )
                    # 过滤到指定日期范围
                    if not data.empty:
                        data = data.loc[request.start_date:request.end_date]
                print(f"方法3完成，数据行数: {len(data)}")
            except Exception as e:
                print(f"方法3失败: {e}")
        
        if data.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"无法获取 {ticker} 的数据。可能原因：1)股票代码不存在 2)日期范围无效 3)Yahoo Finance服务暂时不可用"
            )

        # 2. 运行回测引擎
        print("开始运行回测引擎...")
        results = run_backtest(data, request.initial_investment, request.monthly_investment)
        print("回测完成")
        
        # 3. 返回结果
        return results

    except ValueError as e:
        error_msg = f"数据验证错误: {str(e)}"
        print(f"ValueError: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException as e:
        raise e
    except Exception as e:
        error_msg = f"回测过程中发生错误: {str(e)}"
        print(f"Exception: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.options("/api/backtest-multiple")
async def backtest_multiple_options():
    """处理CORS预检请求"""
    return {"message": "OK"}

@app.post("/api/backtest-multiple")
async def do_backtest_multiple(request: MultipleBacktestRequest):
    """执行多个股票的批量回测并返回结果"""
    print(f"收到批量回测请求: {len(request.stocks)} 个股票")
    
    # 验证股票数量
    if len(request.stocks) < 2:
        raise HTTPException(status_code=400, detail="至少需要选择2个股票进行对比")
    if len(request.stocks) > 5:
        raise HTTPException(status_code=400, detail="最多支持5个股票同时对比")
    
    try:
        # 收集每个股票的数据
        stocks_data = []
        for stock in request.stocks:
            ticker = convert_to_yfinance_ticker(stock.stock_code, stock.market)
            print(f"获取 {stock.name} ({ticker}) 的数据...")
            
            # 使用与单个回测相同的多重方法获取数据
            data = pd.DataFrame()
            
            # 方法1: 标准yf.download
            try:
                data = yf.download(
                    ticker, 
                    start=request.start_date, 
                    end=request.end_date, 
                    auto_adjust=True,
                    progress=False,
                    threads=False
                )
            except Exception as e:
                print(f"方法1失败 ({ticker}): {e}")
            
            # 方法2: 使用Ticker对象
            if data.empty:
                try:
                    ticker_obj = yf.Ticker(ticker)
                    data = ticker_obj.history(
                        start=request.start_date,
                        end=request.end_date,
                        auto_adjust=True,
                        timeout=30
                    )
                except Exception as e:
                    print(f"方法2失败 ({ticker}): {e}")
            
            # 检查数据是否为空
            if data.empty:
                print(f"警告: {stock.name} ({ticker}) 无数据，跳过")
                continue
            
            stocks_data.append({
                'code': stock.stock_code,
                'name': stock.name,
                'data': data
            })
        
        if len(stocks_data) < 2:
            raise HTTPException(
                status_code=404, 
                detail="无法获取足够的股票数据进行对比，请检查股票代码和日期范围"
            )
        
        # 执行批量回测
        print(f"开始批量回测 {len(stocks_data)} 个股票...")
        results = backtest_multiple(
            stocks_data, 
            request.initial_investment, 
            request.monthly_investment
        )
        print("批量回测完成")
        
        return results
        
    except HTTPException as e:
        raise e
    except Exception as e:
        error_msg = f"批量回测过程中发生错误: {str(e)}"
        print(f"Exception: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

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