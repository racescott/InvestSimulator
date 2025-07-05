#!/usr/bin/env python3
"""
数据库初始化脚本
用于在Railway部署时初始化PostgreSQL数据库
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3

def init_postgresql_from_sqlite():
    """从SQLite导入数据到PostgreSQL"""
    # 连接PostgreSQL
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("错误: 未找到DATABASE_URL环境变量")
        return False
    
    try:
        # 连接PostgreSQL
        pg_conn = psycopg2.connect(DATABASE_URL)
        pg_cursor = pg_conn.cursor()
        
        # 创建stocks表
        pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                market TEXT NOT NULL,
                yfinance_symbol TEXT NOT NULL
            );
        """)
        
        # 创建索引以提高查询性能
        pg_cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stocks_name ON stocks(name);
            CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(yfinance_symbol);
            CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market);
        """)
        
        # 检查是否已经有数据
        pg_cursor.execute("SELECT COUNT(*) FROM stocks;")
        count = pg_cursor.fetchone()[0]
        
        if count > 0:
            print(f"数据库已存在 {count} 条记录，跳过初始化")
            pg_conn.close()
            return True
        
        # 如果存在本地SQLite文件，从中导入数据
        sqlite_path = 'stocks.db'
        if os.path.exists(sqlite_path):
            print(f"从 {sqlite_path} 导入数据...")
            
            # 连接SQLite
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # 读取SQLite中的数据
            sqlite_cursor.execute("SELECT name, market, yfinance_symbol FROM stocks;")
            rows = sqlite_cursor.fetchall()
            
            # 批量插入到PostgreSQL
            insert_query = """
                INSERT INTO stocks (name, market, yfinance_symbol) 
                VALUES (%s, %s, %s);
            """
            
            batch_size = 1000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                pg_cursor.executemany(insert_query, batch)
                pg_conn.commit()
                print(f"已导入 {min(i + batch_size, len(rows))} / {len(rows)} 条记录")
            
            sqlite_conn.close()
            print(f"成功导入 {len(rows)} 条记录")
            
        else:
            # 如果没有SQLite文件，插入一些测试数据
            print("未找到SQLite文件，插入测试数据...")
            test_data = [
                ('Apple Inc.', 'US', 'AAPL'),
                ('Microsoft Corporation', 'US', 'MSFT'),
                ('Amazon.com Inc.', 'US', 'AMZN'),
                ('Alphabet Inc.', 'US', 'GOOGL'),
                ('Tesla Inc.', 'US', 'TSLA'),
                ('SPDR S&P 500 ETF Trust', 'US', 'SPY'),
                ('Invesco QQQ Trust', 'US', 'QQQ'),
                ('iShares Core S&P 500 ETF', 'US', 'IVV'),
                ('贵州茅台', 'A-Share', '600519.SS'),
                ('中国平安', 'A-Share', '601318.SS'),
            ]
            
            insert_query = """
                INSERT INTO stocks (name, market, yfinance_symbol) 
                VALUES (%s, %s, %s);
            """
            pg_cursor.executemany(insert_query, test_data)
            pg_conn.commit()
            print(f"成功插入 {len(test_data)} 条测试数据")
        
        pg_conn.close()
        print("数据库初始化完成!")
        return True
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    success = init_postgresql_from_sqlite()
    if success:
        print("✅ 数据库初始化成功")
    else:
        print("❌ 数据库初始化失败")
        exit(1)