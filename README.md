# 📈 InvestSimulator

> 股票投资模拟和定投策略回测平台

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Railway-blue)](https://investsimulator.railway.app)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🚀 项目简介

InvestSimulator 是一个全面的股票投资模拟和回测平台，专注于**定投策略(Dollar-Cost Averaging)**的效果分析。通过真实的历史数据，帮助投资者了解定投策略的长期收益表现。

### ✨ 核心特性

- **📊 13,000+ 证券数据库** - 包含美股、A股和934+只ETF
- **🎯 定投策略回测** - 模拟定期定额投资策略
- **📈 可视化分析** - 交互式图表展示投资表现
- **🌍 多市场支持** - 美股、A股、ETF全覆盖
- **📱 响应式设计** - 支持桌面和移动端访问
- **⚡ 实时数据** - 基于yfinance API获取最新数据

## 🎯 投资策略

### 定投策略 (Dollar-Cost Averaging)
- **初始投资**: 一次性投入启动资金
- **定期投资**: 每月固定金额持续投入
- **纯买入策略**: 只买不卖，长期持有
- **基准对比**: 与投入本金(零收益)对比，清晰展示投资效果

## 🏗️ 技术架构

### 后端技术栈
- **FastAPI** - 现代Python Web框架
- **PostgreSQL** - 生产级数据库
- **yfinance** - 金融数据获取
- **pandas** - 数据处理和分析

### 前端技术栈
- **Vue.js 3** - 响应式前端框架
- **ECharts** - 交互式图表库
- **Pico.css** - 轻量级CSS框架
- **现代JavaScript** - ES6+ 语法

### 基础设施
- **Railway** - 云平台部署
- **PostgreSQL** - 云数据库
- **GitHub Actions** - CI/CD (可选)

## 🎮 快速开始

### 在线体验
访问 [Live Demo](https://investsimulator.railway.app) 立即体验

### 本地开发

#### 1. 克隆项目
```bash
git clone https://github.com/racescott/InvestSimulator.git
cd InvestSimulator
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 启动后端服务
```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

#### 4. 启动前端服务
```bash
cd frontend
python3 -m http.server 3000
```

#### 5. 访问应用
- 前端: http://localhost:3000
- API文档: http://localhost:8000/docs

## 📊 支持的投资品种

### 美股 (US Market)
- **大盘股**: AAPL, MSFT, GOOGL, AMZN, TSLA
- **指数ETF**: SPY, QQQ, VTI, IVV
- **行业ETF**: XLK (科技), XLF (金融), XLE (能源)

### A股 (Chinese Market)
- **蓝筹股**: 600519 (茅台), 601318 (平安)
- **成长股**: 腾讯、阿里巴巴等
- **自动识别**: 上交所(.SS)和深交所(.SZ)

### ETF基金 (934+只)
- **传统指数**: S&P 500, 纳斯达克, 全市场
- **主题投资**: AI、区块链、清洁能源
- **杠杆产品**: 2x/3x 多空ETF
- **国际市场**: 新兴市场、发达市场

## 🔧 API 接口

### 主要端点
- `GET /` - 欢迎页面
- `GET /api/search?q={query}` - 搜索股票/ETF
- `GET /api/data/{market}/{code}` - 获取历史数据
- `POST /api/backtest` - 执行定投回测

### 回测请求示例
```json
{
  "market": "US",
  "stock_code": "SPY",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_investment": 10000,
  "monthly_investment": 1000
}
```

## 📈 使用示例

### 保守型投资组合
```
标的: SPY (标普500ETF)
初始投资: $10,000
月投: $1,000
预期年化收益: 8-10%
```

### 成长型投资组合
```
标的: QQQ (纳斯达克100ETF)
初始投资: $5,000
月投: $500
预期年化收益: 10-12%
```

### 创新型投资组合
```
标的: ARKK (ARK创新ETF)
初始投资: $2,000
月投: $200
预期年化收益: 高波动
```

## 🚀 部署到Railway

### 1. 一键部署
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/InvestSimulator)

### 2. 手动部署
1. Fork此项目到你的GitHub
2. 在Railway连接GitHub仓库
3. 添加PostgreSQL数据库
4. 自动部署完成

### 3. 环境变量
- `DATABASE_URL` - PostgreSQL连接字符串 (自动设置)
- `PORT` - 应用端口 (自动设置)

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发流程
1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

### 代码规范
- 使用Python 3.8+
- 遵循PEP 8规范
- 添加适当的注释
- 确保测试通过

## 📝 许可证

本项目基于 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [yfinance](https://github.com/ranaroussi/yfinance) - 金融数据API
- [FastAPI](https://fastapi.tiangolo.com) - 现代Python Web框架
- [Vue.js](https://vuejs.org) - 渐进式JavaScript框架
- [ECharts](https://echarts.apache.org) - 数据可视化库
- [Railway](https://railway.app) - 云平台部署

## 📧 联系方式

- 作者: racescott
- 项目地址: https://github.com/racescott/InvestSimulator
- 在线演示: https://investsimulator.railway.app

---

**⚠️ 投资风险提示**: 本平台仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。