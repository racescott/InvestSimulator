# 📈 InvestSimulator

> 股票定投策略回测平台 - 真实数据，专业分析

[![Live Demo](https://img.shields.io/badge/🌐_立即体验-Railway-blue)](https://investsimulator.up.railway.app/app)
[![Deployment Status](https://img.shields.io/badge/状态-✅_在线-success)](https://investsimulator.up.railway.app/app)
[![Data Coverage](https://img.shields.io/badge/数据覆盖-13K+_证券-orange)](https://investsimulator.up.railway.app/app)

**立即体验**: [https://investsimulator.up.railway.app/app](https://investsimulator.up.railway.app/app)

## 📋 功能特色

- **💰 定投策略回测** - 模拟定期定额投资，分析长期收益
- **📊 13,097+ 证券数据** - 覆盖美股、A股、ETF全市场
- **📈 专业图表分析** - 交互式ECharts可视化投资表现  
- **📱 全端适配** - 桌面、平板、手机完美支持
- **⚡ 实时数据** - Yahoo Finance API提供最新行情

## 💡 投资策略

**定投回测 (Dollar-Cost Averaging)**
- 🏦 初始投资 + 📅 月度定投 = 📈 长期收益分析
- 📊 与投入本金对比，直观显示投资效果
- 🎯 验证定投策略在不同市场环境下的表现

## 🛠️ 技术栈

**后端**: FastAPI + PostgreSQL + yfinance  
**前端**: Vue.js + ECharts + Pico.css  
**部署**: Railway云平台 + GitHub自动部署

## 🚀 使用指南

### 在线使用
1. 访问 [https://investsimulator.up.railway.app/app](https://investsimulator.up.railway.app/app)
2. 搜索股票：输入代码或名称（如：AAPL、SPY、茅台、600519）
3. 设置参数：选择时间范围、初始投资、月投金额
4. 开始回测：点击"开始定投回测"查看结果

### 本地开发
```bash
git clone https://github.com/racescott/InvestSimulator.git
cd InvestSimulator
pip install -r requirements.txt

# 启动后端 (需要PostgreSQL)
cd backend && uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 启动前端
cd frontend && python3 -m http.server 3000
```

## 📊 数据覆盖

**13,097+ 全球证券数据** | **涵盖主流投资品种**

🇺🇸 **美股市场**: 个股 + 934+只ETF (传统指数、行业主题、杠杆产品)  
🇨🇳 **A股市场**: 沪深两市全覆盖，自动识别交易所代码  
🌍 **国际ETF**: 新兴市场、发达市场、商品、债券基金

*支持按股票代码或公司名称搜索，如：AAPL、茅台、SPY等*

## 📈 回测示例

**保守型策略**: SPY + 10,000初始 + 1,000月投 → 验证指数基金长期表现  
**成长型策略**: QQQ + 5,000初始 + 500月投 → 科技股集中投资效果  
**主题型策略**: ARKK + 2,000初始 + 200月投 → 创新主题高波动分析

## 🚀 自部署

**一键部署到Railway**
1. Fork项目到GitHub
2. 在Railway连接仓库  
3. 添加PostgreSQL服务
4. 自动部署完成

## 📄 开源协议

MIT License - 欢迎Fork和贡献代码

## 📧 联系信息

**作者**: racescott | **GitHub**: [InvestSimulator](https://github.com/racescott/InvestSimulator)  
**在线演示**: https://investsimulator.up.railway.app/app

---

**⚠️ 免责声明**: 本平台仅供学习研究，不构成投资建议。投资有风险，决策需谨慎。