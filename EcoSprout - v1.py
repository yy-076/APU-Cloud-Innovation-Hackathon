# ===== 导入所需的库 =====
# sys / asyncio：修复 Windows 上的事件循环问题；time：Gemini 繁忙时等待重试
import sys
import asyncio
import time

# 仅在 Windows 上：改用 Selector 事件循环，减少终端里的 ConnectionResetError 报错
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# streamlit：网页界面；genai：调用 Gemini；random：模拟传感器数据
# fpdf：生成 PDF 报告；tempfile / os：临时文件；numpy / pandas：数据处理与图表
import streamlit as st
from google import genai
import random
from fpdf import FPDF
import tempfile
import os
import numpy as np
import pandas as pd

# 把 Gemini 的原始错误转换成用户看得懂的提示
# 原始错误仍会打印在 PyCharm 终端里，方便调试
def friendly_error(err):
    print(f"[Gemini error] {err}")
    msg = str(err)
    if "API key" in msg or "API_KEY" in msg or "PERMISSION_DENIED" in msg:
        return "🔑 Your Gemini API key doesn't seem to work. Please check it in the sidebar and try again."
    if "503" in msg or "UNAVAILABLE" in msg:
        return "😅 Oops! Gemini is busy right now because lots of people are using it. Please wait a moment and try again."
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        return "⏳ Oops! You've reached the Gemini usage limit. Please wait a minute and try again."
    if "504" in msg or "DEADLINE_EXCEEDED" in msg or "timed out" in msg.lower():
        return "⌛ Gemini took too long to respond. Please try again."
    if "404" in msg or "NOT_FOUND" in msg:
        return "🤖 This Gemini model isn't available anymore. Please update the model name in the code."
    return "⚠️ Oops! Something went wrong while contacting Gemini. Please try again."


# 1. 页面配置：浏览器标签标题、图标、宽屏布局（必须是第一个 Streamlit 指令）
st.set_page_config(
    page_title="EcoSprout | Smart Facility Energy Platform",
    page_icon="⚡",
    layout="wide"
)


# 自定义 CSS 样式：APU 翡翠绿 + 海军蓝主题
st.markdown("""
    <style>
    /* ========== 0. 设计变量 (Design tokens) ========== */
    .stApp {
        --apu-green: #008751;
        --apu-emerald: #10b981;
        --apu-mint: #34d399;
        --apu-blue: #2563eb;
        /* 卡片背景：浅色模式是半透明白，深色模式是半透明深蓝 */
        --card-bg: light-dark(rgba(255, 255, 255, 0.86), rgba(19, 35, 58, 0.72));
        --card-border: light-dark(rgba(0, 135, 81, 0.16), rgba(52, 211, 153, 0.16));
        --card-shadow: 0 14px 34px -18px light-dark(rgba(15, 29, 48, 0.28), rgba(0, 0, 0, 0.75));
        --muted: light-dark(#4b6075, #94a8be);
        --accent: light-dark(#008751, #34d399);
    }

    /* ========== 1. 页面背景：光晕 + 校园剪影图 + 网格点 (不再是纯白) ========== */
    .stApp {
        background-image:
            radial-gradient(1100px 520px at 105% -8%, light-dark(rgba(16, 185, 129, 0.20), rgba(16, 185, 129, 0.16)), transparent 62%),
            radial-gradient(900px 600px at -8% 108%, light-dark(rgba(37, 99, 235, 0.13), rgba(59, 130, 246, 0.14)), transparent 60%),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 220' preserveAspectRatio='xMidYMax meet'%3E%3Cg fill='%2310b981' fill-opacity='0.09'%3E%3Crect x='0' y='140' width='72' height='80' rx='3'/%3E%3Crect x='78' y='80' width='46' height='140' rx='3'/%3E%3Crect x='100' y='54' width='3' height='26'/%3E%3Crect x='138' y='80' width='46' height='140' rx='3'/%3E%3Crect x='160' y='54' width='3' height='26'/%3E%3Crect x='190' y='100' width='90' height='120' rx='3'/%3E%3Crect x='234' y='74' width='3' height='26'/%3E%3Crect x='286' y='100' width='110' height='120' rx='3'/%3E%3Crect x='340' y='74' width='3' height='26'/%3E%3Crect x='410' y='140' width='46' height='80' rx='3'/%3E%3Crect x='470' y='80' width='46' height='140' rx='3'/%3E%3Cpath d='M522 220V150Q612 70 702 150V220Z'/%3E%3Crect x='712' y='140' width='110' height='80' rx='3'/%3E%3Crect x='766' y='114' width='3' height='26'/%3E%3Crect x='828' y='160' width='110' height='60' rx='3'/%3E%3Crect x='952' y='160' width='58' height='60' rx='3'/%3E%3Crect x='1024' y='125' width='58' height='95' rx='3'/%3E%3Crect x='1052' y='99' width='3' height='26'/%3E%3Crect x='1096' y='80' width='46' height='140' rx='3'/%3E%3Crect x='1118' y='54' width='3' height='26'/%3E%3Crect x='1148' y='55' width='90' height='165' rx='3'/%3E%3Crect x='1248' y='80' width='90' height='140' rx='3'/%3E%3Crect x='1348' y='140' width='72' height='80' rx='3'/%3E%3Crect x='1434' y='160' width='58' height='60' rx='3'/%3E%3Crect x='1506' y='125' width='90' height='95' rx='3'/%3E%3Crect x='1178' y='60' width='5' height='160'/%3E%3Cpath transform='rotate%280 1180 60%29' d='M1180 60 L1175 8 Q1180 0 1185 8Z'/%3E%3Cpath transform='rotate%28120 1180 60%29' d='M1180 60 L1175 8 Q1180 0 1185 8Z'/%3E%3Cpath transform='rotate%28240 1180 60%29' d='M1180 60 L1175 8 Q1180 0 1185 8Z'/%3E%3Crect x='1298' y='60' width='5' height='160'/%3E%3Cpath transform='rotate%280 1300 60%29' d='M1300 60 L1295 8 Q1300 0 1305 8Z'/%3E%3Cpath transform='rotate%28120 1300 60%29' d='M1300 60 L1295 8 Q1300 0 1305 8Z'/%3E%3Cpath transform='rotate%28240 1300 60%29' d='M1300 60 L1295 8 Q1300 0 1305 8Z'/%3E%3Crect x='1458' y='60' width='5' height='160'/%3E%3Cpath transform='rotate%280 1460 60%29' d='M1460 60 L1455 8 Q1460 0 1465 8Z'/%3E%3Cpath transform='rotate%28120 1460 60%29' d='M1460 60 L1455 8 Q1460 0 1465 8Z'/%3E%3Cpath transform='rotate%28240 1460 60%29' d='M1460 60 L1455 8 Q1460 0 1465 8Z'/%3E%3Ccircle cx='20' cy='206' r='16'/%3E%3Ccircle cx='160' cy='206' r='16'/%3E%3Ccircle cx='300' cy='206' r='16'/%3E%3Ccircle cx='440' cy='206' r='16'/%3E%3Ccircle cx='580' cy='206' r='16'/%3E%3Ccircle cx='720' cy='206' r='16'/%3E%3Ccircle cx='860' cy='206' r='16'/%3E%3Ccircle cx='1000' cy='206' r='16'/%3E%3Ccircle cx='1140' cy='206' r='16'/%3E%3Ccircle cx='1280' cy='206' r='16'/%3E%3Ccircle cx='1420' cy='206' r='16'/%3E%3Ccircle cx='1560' cy='206' r='16'/%3E%3C/g%3E%3C/svg%3E"),
            radial-gradient(light-dark(rgba(0, 135, 81, 0.13), rgba(148, 163, 184, 0.09)) 1px, transparent 1.6px);
        background-size: auto, auto, 100% auto, 24px 24px;
        background-position: 0 0, 0 0, center bottom, 0 0;
        background-repeat: no-repeat, no-repeat, no-repeat, repeat;
        background-attachment: fixed;
    }

    /* 顶部工具栏：半透明毛玻璃，背景图能透出来，滚动时也不会挡住文字 */
    [data-testid="stHeader"] {
        background: light-dark(rgba(238, 246, 241, 0.72), rgba(10, 20, 36, 0.72));
        backdrop-filter: blur(10px);
    }

    /* 主内容区：限制最大宽度，排版更整齐 */
    [data-testid="stMainBlockContainer"] {
        max-width: 1380px;
        padding-top: 2.4rem;
    }

    /* 页脚：用 CSS 伪元素生成，不改动任何 Python 逻辑 */
    [data-testid="stMainBlockContainer"]::after {
        content: "EcoSprout · Made with 🍄 by Team Mushroom · Powered by Google Cloud & Gemini";
        display: block;
        margin-top: 3.5rem;
        padding-top: 1.1rem;
        border-top: 1px solid var(--card-border);
        text-align: center;
        font-size: 0.8rem;
        letter-spacing: 0.04em;
        color: var(--muted);
    }

    /* ========== 2. 侧边栏 (Sidebar)：APU 深蓝 + 绿色光晕 ========== */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(16, 185, 129, 0.35);
        box-shadow: 6px 0 28px -14px rgba(0, 0, 0, 0.55);
        background-image:
            radial-gradient(420px 320px at 0% 0%, rgba(16, 185, 129, 0.20), transparent 70%),
            radial-gradient(380px 300px at 100% 100%, rgba(37, 99, 235, 0.16), transparent 70%);
    }

    /* 侧边栏顶部品牌卡片（纯 CSS 生成） */
    [data-testid="stSidebarUserContent"]::before {
        content: "🌱  ECOSPROUT\\A Energy Command Center";
        white-space: pre-line;
        display: block;
        margin: 0 0 1.3rem;
        padding: 0.95rem 1.1rem;
        border-radius: 14px;
        background: linear-gradient(135deg, #008751 0%, #0b5c4a 55%, #14233c 100%);
        border: 1px solid rgba(52, 211, 153, 0.35);
        box-shadow: 0 12px 26px -14px rgba(16, 185, 129, 0.8);
        color: #ecfdf5;
        font-size: 0.92rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        line-height: 1.55;
    }

    /* 侧边栏小标题：改成小号大写标签，更有层次感 */
    section[data-testid="stSidebar"] h3 {
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #a7f3d0 !important;
        opacity: 0.85;
        padding: 0.2rem 0 0.15rem !important;
    }

    section[data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
    }

    section[data-testid="stSidebar"] hr {
        margin: 1rem 0;
        border-color: rgba(148, 163, 184, 0.18);
    }

    /* 侧边栏导航按钮：文字左对齐，悬停时左侧亮绿条 + 轻微右移 */
    section[data-testid="stSidebar"] [data-testid="stButton"] button {
        justify-content: flex-start;
        text-align: left;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 12px;
        padding: 0.55rem 0.85rem;
        transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    }

    section[data-testid="stSidebar"] [data-testid="stButton"] button > div {
        justify-content: flex-start;
        width: 100%;
    }

    section[data-testid="stSidebar"] [data-testid="stButton"] button p {
        text-align: left;
        font-weight: 500;
    }

    section[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.30), rgba(16, 185, 129, 0.06));
        border-color: rgba(52, 211, 153, 0.6);
        box-shadow: inset 3px 0 0 #34d399;
        transform: translateX(3px);
        color: #ffffff;
    }

    /* ========== 3. APU 顶部横幅 (Hero banner) ========== */
    .apu-header {
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 28px;
        padding: 30px 38px 34px;
        margin-bottom: 30px;
        border-radius: 22px;
        color: #ffffff;
        border: 1px solid rgba(52, 211, 153, 0.25);
        background:
            radial-gradient(520px 260px at 82% 18%, rgba(52, 211, 153, 0.32), transparent 70%),
            radial-gradient(circle, rgba(255, 255, 255, 0.07) 1px, transparent 1.5px) 0 0 / 18px 18px,
            linear-gradient(115deg, #0b1628 0%, #14233c 38%, #006b41 78%, #008751 100%);
        box-shadow: 0 26px 50px -26px rgba(0, 135, 81, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    /* 横幅底部流动的渐变光条 */
    .apu-header::after {
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 4px;
        background: linear-gradient(90deg, #10b981, #34d399, #60a5fa, #10b981);
        background-size: 200% 100%;
        animation: apu-flow 6s linear infinite;
    }

    .apu-header-text {
        position: relative;
        z-index: 1;
        max-width: 780px;
    }

    .apu-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 14px;
        padding: 5px 12px;
        border-radius: 999px;
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid rgba(52, 211, 153, 0.35);
        color: #a7f3d0;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    /* "LIVE" 呼吸灯小圆点 */
    .apu-live-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #34d399;
        animation: apu-pulse 1.8s ease-out infinite;
    }

    .apu-header h1 {
        color: #ffffff !important;
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        line-height: 1.2 !important;
        margin: 0 0 10px !important;
        padding: 0 !important;
    }

    .apu-header p {
        color: #d1fae5 !important;
        font-size: 1.02rem;
        margin: 0 0 18px !important;
    }

    .apu-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .apu-badges span {
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.16);
        color: #ecfdf5;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* 横幅右侧的校园插画（SVG 图片） */
    .apu-hero-art {
        position: relative;
        z-index: 1;
        width: 340px;
        flex-shrink: 0;
        filter: drop-shadow(0 14px 24px rgba(0, 0, 0, 0.28));
    }

    /* 风力发电机叶片旋转动画 */
    .apu-turbine {
        transform-box: view-box;
        transform-origin: 318px 74px;
        animation: apu-spin 7s linear infinite;
    }

    /* 屏幕较窄时隐藏插画，避免挤压标题 */
    @media (max-width: 1100px) {
        .apu-hero-art { display: none; }
    }

    /* ========== 4. 章节标题：左侧绿蓝渐变竖条 ========== */
    [data-testid="stMain"] h3 {
        position: relative;
        padding-left: 0.95rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stMain"] h3::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0.55em;
        bottom: 0.55em;
        width: 4px;
        border-radius: 4px;
        background: linear-gradient(180deg, var(--apu-emerald), var(--apu-blue));
    }

    [data-testid="stMain"] h4 {
        color: var(--accent) !important;
    }

    /* 分隔线：渐变细线代替灰线 */
    [data-testid="stMain"] hr {
        border: none !important;
        height: 2px;
        margin: 1.6rem 0;
        background: linear-gradient(90deg, transparent, var(--accent), var(--apu-blue), transparent);
        opacity: 0.45;
    }

    /* ========== 5. 指标卡片 (Metric cards)：玻璃卡片 + 顶部彩条 ========== */
    /* 注意：新版 Streamlit 的指标卡片叫 stMetric，旧选择器 metric-container 已经失效 */
    [data-testid="stMetric"] {
        position: relative;
        overflow: hidden;
        padding: 20px 22px 16px;
        border-radius: 18px;
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        box-shadow: var(--card-shadow);
        backdrop-filter: blur(6px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    [data-testid="stMetric"]::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--apu-green), var(--apu-mint), var(--apu-blue));
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
    }

    [data-testid="stMetricLabel"] p {
        color: var(--muted) !important;
        font-size: 0.76rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.07em;
        text-transform: uppercase;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700;
    }

    /* ========== 6. 表格、图表、展开框：统一卡片风格 ========== */
    [data-testid="stDataFrame"] {
        box-shadow: var(--card-shadow);
    }

    /* 图表卡片背景要和主题背景色一致 (与 config.toml 的 backgroundColor 对应)，否则图表会有色块 */
    [data-testid="stElementContainer"]:has([data-testid="stVegaLiteChart"]) {
        box-sizing: border-box;
        padding: 18px 16px 10px;
        border-radius: 18px;
        background: light-dark(#eef6f1, #0a1424);
        border: 1px solid var(--card-border);
        box-shadow: var(--card-shadow);
    }

    [data-testid="stExpander"] details {
        border-radius: 18px;
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        box-shadow: var(--card-shadow);
    }

    [data-testid="stExpander"] summary {
        font-weight: 600;
    }

    /* 提示框 (info / success / warning / error)：圆角 + 左侧同色强调条 */
    [data-testid="stAlertContainer"] {
        border-radius: 14px;
        border-left: 4px solid currentColor;
        box-shadow: 0 8px 22px -16px rgba(0, 0, 0, 0.45);
    }

    /* 演示模式勾选框：做成虚线小卡片，更显眼 */
    [data-testid="stMain"] [data-testid="stCheckbox"] {
        width: fit-content;
        padding: 0.6rem 1rem;
        border-radius: 12px;
        background: var(--card-bg);
        border: 1px dashed var(--accent);
    }

    /* ========== 7. 主区域按钮：绿蓝渐变 + 悬停上浮 ========== */
    [data-testid="stMain"] [data-testid="stBaseButton-secondary"] {
        padding: 0.65rem 1.25rem;
        border: 0;
        border-radius: 12px;
        background: linear-gradient(135deg, #008751 0%, #0b7a6e 55%, #1d4ed8 140%);
        color: #ffffff;
        box-shadow: 0 12px 24px -14px rgba(0, 135, 81, 0.95);
        transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
    }

    [data-testid="stMain"] [data-testid="stBaseButton-secondary"] p {
        color: #ffffff !important;
        font-weight: 600;
    }

    [data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover {
        transform: translateY(-2px);
        filter: brightness(1.1);
        color: #ffffff;
        box-shadow: 0 16px 28px -14px rgba(0, 135, 81, 1);
    }

    [data-testid="stMain"] [data-testid="stBaseButton-secondary"]:active {
        transform: translateY(0);
    }

    [data-testid="stMain"] [data-testid="stBaseButton-secondary"]:focus-visible {
        outline: 2px solid var(--apu-mint);
        outline-offset: 2px;
    }

    /* 并排的按钮（执行器控制、异常处理）做成等宽大方块 */
    [data-testid="stMain"] [data-testid="stColumn"] [data-testid="stElementContainer"]:has([data-testid="stButton"]),
    [data-testid="stMain"] [data-testid="stColumn"] [data-testid="stButton"],
    [data-testid="stMain"] [data-testid="stColumn"] [data-testid="stButton"] button {
        width: 100%;
        min-height: 3.6rem;
    }

    /* ========== 8. 动画 ========== */
    /* 切换模块时，内容由下往上淡入 */
    [data-testid="stMain"] [data-testid="stElementContainer"] {
        animation: apu-rise 0.45s ease both;
    }

    @keyframes apu-rise {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: none; }
    }

    @keyframes apu-flow {
        to { background-position: 200% 0; }
    }

    @keyframes apu-spin {
        to { transform: rotate(360deg); }
    }

    @keyframes apu-pulse {
        0% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.7); }
        100% { box-shadow: 0 0 0 10px rgba(52, 211, 153, 0); }
    }

    /* 系统开启“减少动态效果”时关闭所有动画 */
    @media (prefers-reduced-motion: reduce) {
        .stApp *, .stApp *::before, .stApp *::after {
            animation: none !important;
            transition: none !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# APU Header Banner
st.markdown("""
    <div class="apu-header">
        <div class="apu-header-text">
            <div class="apu-eyebrow"><span class="apu-live-dot"></span>Live · Smart Campus Energy Control</div>
            <h1>🌱 EcoSprout</h1>
            <p>Powered by Google Cloud & Gemini AI | Intelligent IoT & Network Telemetry Optimization</p>
            <div class="apu-badges">
                <span>📡 IoT Telemetry</span>
                <span>🤖 Gemini AI Agent</span>
                <span>🚨 Anomaly Triage</span>
                <span>🌱 Carbon Tracking</span>
            </div>
        </div>
        <svg class="apu-hero-art" viewBox="0 0 380 210" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <circle cx="250" cy="70" r="58" fill="#34d399" fill-opacity="0.10"/>
            <line x1="6" y1="196" x2="374" y2="196" stroke="#a7f3d0" stroke-opacity="0.55" stroke-width="2" stroke-linecap="round"/>
            <path d="M58 40 a24 24 0 0 1 42 0" fill="none" stroke="#a7f3d0" stroke-width="3" stroke-linecap="round" stroke-opacity="0.5"/>
            <path d="M67 48 a13 13 0 0 1 24 0" fill="none" stroke="#a7f3d0" stroke-width="3" stroke-linecap="round" stroke-opacity="0.8"/>
            <circle cx="79" cy="56" r="4" fill="#34d399"/>
            <rect x="40" y="66" width="78" height="130" rx="6" fill="#ffffff" fill-opacity="0.12" stroke="#d1fae5" stroke-opacity="0.5"/>
            <g fill="#a7f3d0">
                <rect x="52" y="80" width="12" height="9" rx="1.5" fill-opacity="0.9"/><rect x="73" y="80" width="12" height="9" rx="1.5" fill-opacity="0.35"/><rect x="94" y="80" width="12" height="9" rx="1.5" fill-opacity="0.9"/>
                <rect x="52" y="100" width="12" height="9" rx="1.5" fill-opacity="0.35"/><rect x="73" y="100" width="12" height="9" rx="1.5" fill-opacity="0.9"/><rect x="94" y="100" width="12" height="9" rx="1.5" fill-opacity="0.9"/>
                <rect x="52" y="120" width="12" height="9" rx="1.5" fill-opacity="0.9"/><rect x="73" y="120" width="12" height="9" rx="1.5" fill-opacity="0.9"/><rect x="94" y="120" width="12" height="9" rx="1.5" fill-opacity="0.35"/>
                <rect x="52" y="140" width="12" height="9" rx="1.5" fill-opacity="0.35"/><rect x="73" y="140" width="12" height="9" rx="1.5" fill-opacity="0.9"/><rect x="94" y="140" width="12" height="9" rx="1.5" fill-opacity="0.9"/>
                <rect x="52" y="160" width="12" height="9" rx="1.5" fill-opacity="0.9"/><rect x="73" y="160" width="12" height="9" rx="1.5" fill-opacity="0.35"/><rect x="94" y="160" width="12" height="9" rx="1.5" fill-opacity="0.9"/>
            </g>
            <rect x="70" y="178" width="18" height="18" rx="2" fill="#0b1628" fill-opacity="0.55"/>
            <rect x="124" y="112" width="62" height="84" rx="5" fill="#ffffff" fill-opacity="0.09" stroke="#d1fae5" stroke-opacity="0.4"/>
            <g fill="#93c5fd">
                <rect x="134" y="124" width="42" height="7" rx="2" fill-opacity="0.55"/>
                <rect x="134" y="140" width="42" height="7" rx="2" fill-opacity="0.85"/>
                <rect x="134" y="156" width="42" height="7" rx="2" fill-opacity="0.55"/>
                <rect x="134" y="172" width="42" height="7" rx="2" fill-opacity="0.85"/>
            </g>
            <path d="M194 196 V154 Q234 112 274 154 V196 Z" fill="#ffffff" fill-opacity="0.12" stroke="#d1fae5" stroke-opacity="0.5"/>
            <path d="M206 150 L262 150" stroke="#a7f3d0" stroke-opacity="0.5" stroke-width="2"/>
            <rect x="222" y="170" width="24" height="26" rx="12" fill="#0b1628" fill-opacity="0.5"/>
            <g transform="translate(200 98) skewX(-18)">
                <rect x="0" y="0" width="62" height="20" rx="2" fill="#1d4ed8" fill-opacity="0.75" stroke="#bfdbfe" stroke-opacity="0.8"/>
                <path d="M15.5 0 V20 M31 0 V20 M46.5 0 V20 M0 10 H62" stroke="#bfdbfe" stroke-opacity="0.7"/>
            </g>
            <path d="M226 118 V130 M240 118 V130" stroke="#d1fae5" stroke-opacity="0.6" stroke-width="2"/>
            <line x1="318" y1="196" x2="318" y2="74" stroke="#ecfdf5" stroke-width="4" stroke-linecap="round"/>
            <g class="apu-turbine" fill="#ecfdf5">
                <path d="M318 74 L313 26 Q318 18 323 26 Z"/>
                <path d="M318 74 L313 26 Q318 18 323 26 Z" transform="rotate(120 318 74)"/>
                <path d="M318 74 L313 26 Q318 18 323 26 Z" transform="rotate(240 318 74)"/>
            </g>
            <circle cx="318" cy="74" r="6" fill="#34d399" stroke="#ecfdf5" stroke-width="2"/>
            <path d="M286 196 c-4 -26 14 -40 32 -42 c2 18 -10 36 -32 42 z" fill="#34d399" fill-opacity="0.85"/>
            <path d="M288 194 q10 -18 26 -34" stroke="#065f46" stroke-width="1.5" fill="none"/>
            <circle cx="160" cy="58" r="20" fill="#fbbf24" fill-opacity="0.95"/>
            <path d="M163 44 L152 61 H160 L157 72 L168 55 H160 Z" fill="#0b1628"/>
        </svg>
    </div>
""", unsafe_allow_html=True)


# 2. 侧边栏：API 密钥输入框 + 导航按钮 + 区域选择
st.sidebar.markdown("### 📊 Dashboard")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Navigation Modules")

# session_state 会在每次rerun之间保存数据
if 'nav_mode' not in st.session_state:
    st.session_state.nav_mode = "🏢 Campus-Wide Analytics Overview"

modules = [
    "🏢 Campus-Wide Analytics Overview",
    "📊 Live Zone Telemetry & 24h Trends",
    "🚨 Anomaly Detection & AI Triage",
    "🤖 Gemini AI Audit & PDF Reports",
    "🎛️ Live IoT Actuator Controls",
    "🌱 Sustainability & Cost ROI"
]

# 为每个模块生成一个按钮：点击后记住选中的模块，并立刻重新运行页面
for mod in modules:
    if st.sidebar.button(mod, use_container_width=True, key=f"nav_{mod}"):
        st.session_state.nav_mode = mod
        st.rerun()

# 当前正在显示的模块
nav_mode = st.session_state.nav_mode

st.sidebar.markdown("---")
st.sidebar.markdown("### 📍 Zone Selection")

auditoriums = [f"Auditorium {i}" for i in range(1, 8)]
room_ids = ["03-01", "04-02", "05-03", "06-04", "07-05", "08-06", "09-07"]
blocks = ["A", "B", "C", "D", "E"]
block_rooms = [f"{block}-{room}" for block in blocks for room in room_ids]
all_zones = auditoriums + block_rooms

if nav_mode != "🏢 Campus-Wide Analytics Overview":
    room_choice = st.sidebar.selectbox("Select Campus Zone", all_zones, label_visibility="collapsed")
    if st.sidebar.button("🔄 Refresh Sensor Feed", use_container_width=True):
        st.session_state.feed_refreshed = True
        st.rerun()
else:
    room_choice = "All Campus Zones (Macro View)"

if st.session_state.pop("feed_refreshed", False):
    st.toast(f"Sensor feed refreshed for {room_choice}", icon="🔄")

# 初始化缓存：传感器数据、Gemini 根因解释、Gemini 审计报告
if 'telemetry_cache' not in st.session_state:
    st.session_state.telemetry_cache = {}
if 'ai_explanation' not in st.session_state:
    st.session_state.ai_explanation = None
if 'audit_response' not in st.session_state:
    st.session_state.audit_response = None

# 每个区域只随机生成一次模拟传感器数据并存入缓存
cache_key = f"telemetry_{room_choice}"
if cache_key not in st.session_state.telemetry_cache:
    st.session_state.telemetry_cache[cache_key] = {
        "occupancy": random.randint(5, 120),
        "temp": round(random.uniform(20.5, 26.0), 1),
        "ac": random.choice(["AUTO (24°C)", "ON (21°C)", "ECO (25°C)", "ON (19°C)"]),
        "devices": random.randint(10, 150)
    }

current_zone = st.session_state.telemetry_cache[cache_key]

# TAB 1: CAMPUS-WIDE ANALYTICS OVERVIEW
if nav_mode == "🏢 Campus-Wide Analytics Overview":
    st.subheader("🏢 Campus-Wide Energy Distribution & Macro Analytics")
    st.markdown("Macro-level telemetry aggregation across APU campus facilities:")

    summary_df = pd.DataFrame({
        "Zone Category": ["Auditoriums (1-7)", "Block A", "Block B", "Block C", "Block D", "Block E"],
        "Active Zones Count": [7, 7, 7, 7, 7, 7],
        "Avg Occupancy (%)": [68, 45, 82, 34, 76, 52],
        "Estimated Power Draw (kW)": [14.2, 8.5, 16.1, 6.8, 12.4, 9.3],
        "HVAC Status": ["Optimized", "Eco-Mode", "High Cooling", "Standby", "Optimized", "Eco-Mode"]
    })

    st.dataframe(summary_df, use_container_width=True)
    st.markdown("### 📊 Power Draw Comparison by Zone Category")
    st.bar_chart(summary_df.set_index("Zone Category")["Estimated Power Draw (kW)"])
    st.info("💡 **Navigation Tip:** Click any module button in the sidebar to perform zone-specific deep-dive audits.")

# TAB 2: LIVE ZONE TELEMETRY & 24H TRENDS
elif nav_mode == "📊 Live Zone Telemetry & 24h Trends":
    st.subheader(f"📊 Live Telemetry Feed: {room_choice}")
    st.markdown("Real-time IoT sensor telemetry streamed directly from building management controllers:")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Occupancy", f"{current_zone['occupancy']} people")
    col2.metric("Room Temperature", f"{current_zone['temp']} °C")
    col3.metric("AC Status", current_zone['ac'])
    col4.metric("Connected Wi-Fi Devices", current_zone['devices'])

    st.markdown("---")
    st.subheader("📈 Historical IoT Trend Simulation (24-Hour Profile)")
    st.markdown(f"Simulated environmental and power consumption profile for **{room_choice}**:")

    # 用区域名称作为随机种子
    np.random.seed(hash(room_choice) % 2026)
    hours = [f"{i:02d}:00" for i in range(24)]
    base_load = np.random.uniform(5.0, 12.0, 24)
    occupancy_multiplier = [1.8 if 9 <= h <= 17 else 0.8 for h in range(24)]
    power_demand = [round(b * m, 2) for b, m in zip(base_load, occupancy_multiplier)]
    temp_trend = [round(22.0 + (p / 4), 1) for p in power_demand]

    trend_df = pd.DataFrame({
        "Hour": hours,
        "Power Demand (kW)": power_demand,
        "Simulated Temperature (°C)": temp_trend
    }).set_index("Hour")
    st.line_chart(trend_df)

# TAB 3: ANOMALY DETECTION & AI TRIAGE
elif nav_mode == "🚨 Anomaly Detection & AI Triage":
    st.subheader(f"🚨 Automated Anomaly Detection & Triage: {room_choice}")
    st.markdown("Continuous background monitoring evaluating energy waste and over-cooling thresholds:")

    simulate_anomaly = st.checkbox("🧪 Enable Demo Mode (Simulate High-Waste Anomaly Scenario)")

    # 演示模式
    if simulate_anomaly:
        anomaly_score = 88
        anomaly_reasons = [
            "High-power HVAC running continuously at 18.5°C in an unoccupied zone.",
            "Anomalous spike in Wi-Fi device density (42 connected devices) relative to zero physical occupants.",
            "Lighting system left at 100% brightness outside operational hours."
        ]
        st.warning(f"🧪 **DEMO MODE ACTIVE** — Simulating critical energy waste in **{room_choice}**")
    else:
        anomaly_score = 0
        anomaly_reasons = []

        # 规则 1：几乎没人却开着空调 → +45 分
        if current_zone['occupancy'] <= 5 and "ON" in current_zone['ac']:
            anomaly_score += 45
            anomaly_reasons.append("High-power HVAC running in near-empty zone.")
        # 规则 2：Wi-Fi 设备数远多于在场人数（可能有设备闲置耗电）→ +35 分
        if current_zone['devices'] > (current_zone['occupancy'] * 3 + 20):
            anomaly_score += 35
            anomaly_reasons.append("Anomalous Wi-Fi device density relative to physical occupancy.")
        # 规则 3：室温低于 21°C，过度制冷 → +20 分
        if current_zone['temp'] < 21.0:
            anomaly_score += 20
            anomaly_reasons.append("Over-cooling threshold breached (< 21°C).")

    # 风险分数 > 40：严重浪费；1-40：轻微低效；0：运行正常
    if anomaly_score > 40:
        st.error(f"⚠️ **High Energy Waste Anomaly Detected!** (Risk Score: {anomaly_score}/100)")
        for reason in anomaly_reasons:
            st.markdown(f"- *Trigger:* {reason}")

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("🤖 Dispatch AI Triage & Auto-Remediate"):
                st.toast(f"Success: Automated patch command sent to BMS for {room_choice}.", icon="⚡")

        # 请 Gemini 生成根因分析，结果存入 session_state
        with col_act2:
            if st.button("🔍 Ask Gemini: Explain Root Cause"):
                if not api_key:
                    st.warning("⚠️ Please enter your Gemini API key in the sidebar configuration first.")
                else:
                    with st.status("Gemini is analyzing system telemetry and diagnostic logs...",
                                   expanded=True) as status:
                        try:
                            client = genai.Client(api_key=api_key)
                            explanation_prompt = f"""
                            You are an expert Facility Systems Diagnostic Engineer at APU.
                            An energy waste anomaly was flagged in {room_choice} with a risk score of {anomaly_score}/100.
                            Trigger factors:
                            {chr(10).join(['- ' + r for r in anomaly_reasons])}  # <--- FIXED: Added missing closing parenthesis here

                            Provide a brief, professional engineering explanation detailing:
                            1. What went wrong operationally in this zone.
                            2. The estimated financial and carbon impact if left uncorrected.
                            3. The recommended corrective action for the facility team.
                            Keep it concise and punchy for a hackathon presentation.
                            """
                            exp_response = client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=explanation_prompt,
                            )
                            st.session_state.ai_explanation = exp_response.text
                            status.update(label="Analysis Complete!", state="complete", expanded=False)
                        except Exception as ex:
                            status.update(label="Analysis Failed", state="error", expanded=True)
                            st.error(friendly_error(ex))

    elif anomaly_score > 0:
        st.warning(f"⚡ **Moderate Inefficiency Flagged** (Risk Score: {anomaly_score}/100)")
        for reason in anomaly_reasons:
            st.markdown(f"- *Trigger:* {reason}")
    else:
        st.success(f"✅ **{room_choice} Operating at Peak Efficiency:** No telemetry anomalies detected.")

    # 显示最近一次 Gemini 返回的根因分析
    if st.session_state.ai_explanation:
        st.markdown("---")
        st.info(st.session_state.ai_explanation)

# TAB 4: GEMINI AI AUDIT & PDF REPORTS
elif nav_mode == "🤖 Gemini AI Audit & PDF Reports":
    st.subheader(f"🤖 Gemini AI Energy Optimization Agent: {room_choice}")
    st.markdown(
        "Generate a comprehensive, zone-specific AI audit report complete with downloadable official APU PDF documentation:")


    # 生成 PDF
    def create_pdf_report(zone_name, report_text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_fill_color(0, 135, 81)
        pdf.rect(0, 0, 210, 25, 'F')

        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(10, 7)
        pdf.cell(0, 10, "APU Smart Facility & Energy Optimization Report", 0, 1, "L")

        pdf.set_font("helvetica", "I", 10)
        pdf.set_text_color(220, 252, 231)
        pdf.set_xy(10, 30)
        pdf.cell(0, 10, f"Campus Zone: {zone_name} | Powered by Asia Pacific University (APU)", 0, 1, "L")
        pdf.line(10, 40, 200, 40)

        pdf.set_xy(10, 45)
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(40, 40, 40)

        sanitized_text = (
            report_text.replace("**", "")
            .replace("#", "")
            .replace("≤", "<=")
            .replace("≥", ">=")
            .replace("–", "-")
            .replace("—", "-")
        )
        clean_text = sanitized_text.encode('latin-1', 'ignore').decode('latin-1')
        pdf.multi_cell(0, 7, clean_text)

        # 保存为临时 PDF 文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_file.name)
        return temp_file.name


    if st.button("Run AI Energy Audit & Action Plan"):
        if not api_key:
            st.warning(
                "⚠️ Please enter your Gemini API key in the sidebar configuration first before running an audit.")
        else:
            with st.status(f"Analyzing IoT telemetry and network traffic for {room_choice}...",
                           expanded=True) as status:
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""
                    You are an expert AI Smart Facility and Energy Optimization Agent for APU campus.
                    Analyze the following live IoT telemetry for {room_choice}:
                    - Occupancy: {current_zone['occupancy']} people
                    - Room Temperature: {current_zone['temp']} °C
                    - AC Status: {current_zone['ac']}
                    - Connected Wi-Fi Devices: {current_zone['devices']}

                    Provide a structured energy optimization action plan, including:
                    1. An immediate energy-saving recommendation (e.g., adjusting AC temperature or shutting off idle power).
                    2. An anomaly or efficiency score assessment.
                    3. Automated smart schedule adjustments.
                    Keep it professional, concise, and structured with clear headings and bullet points.
                    """

                    # max尝试 3 次：遇到 503（服务器繁忙）就等 2 秒再试，其他错误直接抛出
                    response = None
                    for attempt in range(3):
                        try:
                            response = client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=prompt,
                            )
                            break
                        except Exception as err:
                            if "503" in str(err) and attempt < 2:
                                time.sleep(2)
                                continue
                            else:
                                raise err

                    status.update(label="Analysis Complete!", state="complete", expanded=False)
                    st.session_state.audit_response = response.text

                except Exception as e:
                    status.update(label="Analysis Failed", state="error", expanded=True)
                    st.error(friendly_error(e))

    # 报告生成后显示在可展开的框里，提供download下载按钮
    if st.session_state.audit_response:
        with st.expander(f"📋 View Generated Energy Audit Report: {room_choice}", expanded=True):
            st.markdown(st.session_state.audit_response)

            pdf_path = create_pdf_report(room_choice, st.session_state.audit_response)
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()

            st.markdown("---")
            st.download_button(
                label="📥 Download Official APU Audit Report (PDF)",
                data=pdf_bytes,
                file_name=f"APU_Energy_Audit_{room_choice.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

# TAB 5: LIVE IoT ACTUATOR CONTROLS
elif nav_mode == "🎛️ Live IoT Actuator Controls":
    st.subheader(f"🎛️ Live Facility & IoT Actuator Controls: {room_choice}")
    st.markdown(
        f"Direct hardware command interface communicating with building automation controllers for **{room_choice}**:")

    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        if st.button("⚡ Force Eco-Mode (HVAC)"):
            st.toast(f"Success: Eco-mode broadcasted to {room_choice} HVAC controllers (Target: 25.5°C).", icon="✅")

    with col_btn2:
        if st.button("🔒 Deep Sleep Unoccupied Zones"):
            st.toast(f"Success: Perimeter peripheral power locked down for {room_choice}.", icon="🛡️")

    with col_btn3:
        if st.button("🔄 Flush Fresh Air (DCV)"):
            st.toast(f"Success: Outdoor air dampers opened to 100% for {room_choice}.", icon="🌬️")

    st.markdown("---")
    st.info(
        "💡 **Actuator Feedback:** Executing these commands triggers instant telemetry updates on building management servers.")

# TAB 6: SUSTAINABILITY & COST ROI
elif nav_mode == "🌱 Sustainability & Cost ROI":
    st.subheader(f"🌱 Real-Time Carbon & Cost-Savings Impact: {room_choice}")
    st.markdown("Calculated financial savings and carbon footprint offset based on active zone telemetry:")

    # 按空调模式估算功率
    base_power_kw = 12.5 if "ON" in current_zone['ac'] else 6.0
    if "ECO" in current_zone['ac'] or "AUTO" in current_zone['ac']:
        base_power_kw = 8.0

    # 假设
    hours_active = 12
    daily_kwh = base_power_kw * hours_active
    cost_myr = daily_kwh * 0.50
    carbon_kg = daily_kwh * 0.58

    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.metric("Est. Daily Power Consumption", f"{round(daily_kwh, 1)} kWh",
                  delta=f"-{round(daily_kwh * 0.25, 1)} kWh with AI Eco-Mode", delta_color="inverse")
    col_c2.metric("Est. Daily Energy Cost (RM)", f"RM {round(cost_myr, 2)}",
                  delta=f"-RM {round(cost_myr * 0.25, 2)} saved", delta_color="inverse")
    col_c3.metric("Carbon Footprint (CO₂)", f"{round(carbon_kg, 1)} kg",
                  delta=f"-{round(carbon_kg * 0.25, 1)} kg offset", delta_color="inverse")

    st.markdown("---")
    st.markdown("#### 🏢 Campus-Wide Scaling Projection")
    scaling_zones = st.slider("Select number of campus zones to scale this AI optimization across:", min_value=1,
                              max_value=50, value=15)

    # 按 30% 节能率推算
    projected_monthly_savings_myr = (cost_myr * 0.30) * 30 * scaling_zones
    projected_annual_carbon_tonnes = (carbon_kg * 0.30 * 365 * scaling_zones) / 1000

    st.success(
        f"💡 **AI Impact Projection:** Scaling this agent across **{scaling_zones} APU zones** saves approximately **RM {projected_monthly_savings_myr:,.2f} per month** and reduces campus carbon output by **{projected_annual_carbon_tonnes:,.1f} tonnes of CO₂ annually**!")
