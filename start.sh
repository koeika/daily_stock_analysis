#!/bin/bash
# -*- coding: utf-8 -*-
#
# 🚀 快速启动脚本
# 提供常用操作的快捷命令

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示菜单
show_menu() {
    echo ""
    echo "======================================================"
    echo "  📊 A股智能分析系统 - 快速启动菜单"
    echo "======================================================"
    echo ""
    echo "  【分析功能】"
    echo "  1) 完整分析（股票 + 大盘）- 立即推送到飞书"
    echo "  2) 仅分析股票"
    echo "  3) 仅大盘复盘"
    echo ""
    echo "  【测试功能】"
    echo "  4) 测试飞书推送（简单消息）"
    echo "  5) 发送样例分析报告"
    echo "  6) 数据获取测试（不分析）"
    echo ""
    echo "  【定时任务】"
    echo "  7) 启动定时任务（每天18:00自动执行）"
    echo "  8) 查看定时任务配置"
    echo ""
    echo "  【系统管理】"
    echo "  9) 查看最近日志"
    echo "  10) 查看配置信息"
    echo "  11) 安装/更新依赖"
    echo ""
    echo "  0) 退出"
    echo ""
    echo "======================================================"
    echo -n "请选择操作 [0-11]: "
}

# 检查 Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "未找到 python3,请先安装 Python 3.10+"
        exit 1
    fi
}

# 检查依赖
check_dependencies() {
    if ! python3 -c "import requests" 2>/dev/null; then
        print_warning "检测到缺少依赖,正在安装..."
        pip3 install -r requirements.txt
    fi
}

# 检查 .env 配置
check_env() {
    if [ ! -f ".env" ]; then
        print_error ".env 文件不存在"
        print_info "请先复制 .env.example 并配置："
        echo "    cp .env.example .env"
        echo "    vim .env"
        exit 1
    fi
}

# 1. 完整分析
full_analysis() {
    print_info "开始完整分析（股票 + 大盘）..."
    echo ""
    python3 main.py
    print_success "分析完成!"
}

# 2. 仅分析股票
stocks_only() {
    print_info "开始股票分析（不包含大盘复盘）..."
    echo ""
    python3 main.py --no-market-review
    print_success "分析完成!"
}

# 3. 仅大盘复盘
market_only() {
    print_info "开始大盘复盘..."
    echo ""
    python3 main.py --market-review
    print_success "复盘完成!"
}

# 4. 测试飞书推送
test_feishu() {
    print_info "测试飞书推送..."
    echo ""
    python3 test_feishu_simple.py
}

# 5. 发送样例分析
sample_analysis() {
    print_info "发送样例分析报告到飞书..."
    echo ""
    python3 send_sample_analysis.py
}

# 6. 数据获取测试
dry_run() {
    print_info "数据获取测试（不进行AI分析）..."
    echo ""
    python3 main.py --dry-run
    print_success "测试完成!"
}

# 7. 启动定时任务
start_schedule() {
    print_info "启动定时任务..."
    
    # 检查配置
    if ! grep -q "SCHEDULE_ENABLED=true" .env; then
        print_warning "定时任务未启用"
        echo ""
        echo "请先修改 .env 文件:"
        echo "    SCHEDULE_ENABLED=true"
        echo "    SCHEDULE_TIME=18:00"
        echo ""
        echo -n "是否现在修改? [y/N]: "
        read -r answer
        if [[ "$answer" =~ ^[Yy]$ ]]; then
            sed -i.bak 's/SCHEDULE_ENABLED=false/SCHEDULE_ENABLED=true/' .env
            print_success "已启用定时任务"
        else
            return
        fi
    fi
    
    echo ""
    print_info "启动定时服务（程序会保持运行）..."
    print_warning "按 Ctrl+C 停止服务"
    echo ""
    
    python3 main.py --schedule
}

# 8. 查看定时任务配置
show_schedule_config() {
    print_info "定时任务配置:"
    echo ""
    
    if grep -q "SCHEDULE_ENABLED=true" .env; then
        print_success "定时任务: 已启用"
        schedule_time=$(grep "SCHEDULE_TIME=" .env | cut -d'=' -f2)
        echo "    执行时间: $schedule_time"
    else
        print_warning "定时任务: 未启用"
        echo "    启用方式: 选择菜单选项 7"
    fi
    
    echo ""
    market_enabled=$(grep "MARKET_REVIEW_ENABLED=" .env | cut -d'=' -f2)
    if [ "$market_enabled" = "true" ]; then
        print_success "大盘复盘: 已启用"
    else
        print_warning "大盘复盘: 未启用"
    fi
    
    echo ""
}

# 9. 查看最近日志
show_logs() {
    print_info "最近日志 (最后30行):"
    echo ""
    
    if [ -d "logs" ] && [ "$(ls -A logs/*.log 2>/dev/null)" ]; then
        tail -30 logs/stock_analysis_*.log 2>/dev/null || print_warning "无日志文件"
    else
        print_warning "logs 目录为空"
    fi
}

# 10. 查看配置信息
show_config() {
    print_info "当前配置:"
    echo ""
    
    echo "【AI 配置】"
    if grep -q "GEMINI_API_KEY=.*[^[:space:]]" .env 2>/dev/null; then
        print_success "  Gemini API: 已配置"
    else
        print_warning "  Gemini API: 未配置"
    fi
    
    if grep -q "OPENAI_API_KEY=.*[^[:space:]]" .env 2>/dev/null; then
        print_success "  OpenAI API: 已配置"
        model=$(grep "OPENAI_MODEL=" .env | cut -d'=' -f2)
        echo "    模型: $model"
    else
        print_warning "  OpenAI API: 未配置"
    fi
    
    echo ""
    echo "【通知渠道】"
    if grep -q "FEISHU_WEBHOOK_URL=.*[^[:space:]]" .env 2>/dev/null; then
        print_success "  飞书: 已配置"
    else
        print_warning "  飞书: 未配置"
    fi
    
    if grep -q "WECHAT_WEBHOOK_URL=.*[^[:space:]]" .env 2>/dev/null; then
        print_success "  企业微信: 已配置"
    else
        print_warning "  企业微信: 未配置"
    fi
    
    echo ""
    echo "【股票列表】"
    stock_list=$(grep "STOCK_LIST=" .env | cut -d'=' -f2)
    echo "  $stock_list"
    
    echo ""
}

# 11. 安装依赖
install_deps() {
    print_info "安装/更新依赖..."
    echo ""
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
    print_success "依赖安装完成!"
}

# 主程序
main() {
    check_python
    check_env
    
    while true; do
        show_menu
        read -r choice
        echo ""
        
        case $choice in
            1)
                full_analysis
                ;;
            2)
                stocks_only
                ;;
            3)
                market_only
                ;;
            4)
                test_feishu
                ;;
            5)
                sample_analysis
                ;;
            6)
                dry_run
                ;;
            7)
                start_schedule
                ;;
            8)
                show_schedule_config
                ;;
            9)
                show_logs
                ;;
            10)
                show_config
                ;;
            11)
                install_deps
                ;;
            0)
                print_info "再见!"
                exit 0
                ;;
            *)
                print_error "无效选项,请重新选择"
                ;;
        esac
        
        echo ""
        echo "按 Enter 键继续..."
        read -r
    done
}

# 运行主程序
main
