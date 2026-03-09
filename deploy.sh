#!/bin/bash

###############################################################################
# AI Learning Coach - 一键部署脚本
# 
# 功能：
# - 环境检查
# - 构建和启动所有服务（前端、后端、数据库、向量数据库等）
# - 健康检查
# - 日志查看
#
# 使用方法：
#   ./deploy.sh          # 完整部署
#   ./deploy.sh --clean  # 清理并重新部署
#   ./deploy.sh --logs   # 查看日志
#   ./deploy.sh --stop   # 停止服务
###############################################################################

set -e  # 遇到错误立即退出

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

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}║           🚀 AI Learning Coach 部署脚本 🚀                  ║${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 检查必要的命令是否存在
check_requirements() {
    print_info "检查系统环境..."
    
    local missing_tools=()
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "缺少必要的工具: ${missing_tools[*]}"
        print_info "请先安装 Docker 和 Docker Compose"
        exit 1
    fi
    
    print_success "环境检查通过"
}

# 检查.env文件
check_env_file() {
    print_info "检查环境配置..."
    
    if [ ! -f ".env" ]; then
        print_warning ".env 文件不存在，从 .env.example 复制"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "请编辑 .env 文件，配置必要的环境变量（如 API Key）"
            print_warning "按任意键继续..."
            read -n 1 -s
        else
            print_error ".env.example 文件不存在"
            exit 1
        fi
    fi
    
    print_success "环境配置检查完成"
}

# 停止服务
stop_services() {
    print_info "停止所有服务..."
    
    if docker compose version &> /dev/null; then
        docker compose down
    else
        docker-compose down
    fi
    
    print_success "服务已停止"
}

# 清理数据
clean_data() {
    print_warning "⚠️  即将清理所有数据（包括数据库）！"
    print_warning "此操作不可逆，请确认！(yes/no)"
    read -r confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "取消清理操作"
        return
    fi
    
    print_info "清理 Docker 卷和容器..."
    
    if docker compose version &> /dev/null; then
        docker compose down -v --remove-orphans
    else
        docker-compose down -v --remove-orphans
    fi
    
    # 清理构建缓存
    print_info "清理 Docker 构建缓存..."
    docker builder prune -f
    
    print_success "数据清理完成"
}

# 构建并启动服务
deploy_services() {
    print_info "构建并启动所有服务..."
    echo ""
    print_info "服务列表："
    print_info "  - PostgreSQL 数据库"
    print_info "  - Redis 缓存"
    print_info "  - Milvus 向量数据库"
    print_info "  - FastAPI 后端服务"
    print_info "  - Vue3 前端应用"
    print_info "  - Celery 异步任务"
    echo ""
    
    # 构建并启动
    if docker compose version &> /dev/null; then
        docker compose build --no-cache
        docker compose up -d
    else
        docker-compose build --no-cache
        docker-compose up -d
    fi
    
    print_success "服务启动命令已执行"
}

# 等待服务就绪
wait_for_services() {
    print_info "等待服务启动..."
    echo ""
    
    local max_wait=180  # 最长等待3分钟
    local waited=0
    local interval=5
    
    # 等待后端API
    print_info "等待后端 API 就绪..."
    while [ $waited -lt $max_wait ]; do
        if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            print_success "后端 API 已就绪 (http://localhost:8000)"
            break
        fi
        echo -n "."
        sleep $interval
        waited=$((waited + interval))
    done
    
    if [ $waited -ge $max_wait ]; then
        print_error "后端 API 启动超时"
        return 1
    fi
    
    echo ""
    
    # 等待前端
    print_info "等待前端应用就绪..."
    waited=0
    while [ $waited -lt $max_wait ]; do
        if curl -s http://localhost:3000/health > /dev/null 2>&1; then
            print_success "前端应用已就绪 (http://localhost:3000)"
            break
        fi
        echo -n "."
        sleep $interval
        waited=$((waited + interval))
    done
    
    if [ $waited -ge $max_wait ]; then
        print_error "前端应用启动超时"
        return 1
    fi
    
    echo ""
    print_success "所有服务已就绪！"
}

# 健康检查
health_check() {
    print_info "执行健康检查..."
    echo ""
    
    # 检查容器状态
    print_info "容器状态："
    if docker compose version &> /dev/null; then
        docker compose ps
    else
        docker-compose ps
    fi
    
    echo ""
    
    # 检查关键服务
    local services=("ai_coach_db" "ai_coach_redis" "ai_coach_milvus" "ai_coach_app" "ai_coach_frontend")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        if docker ps | grep -q "$service"; then
            local status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null || echo "not_found")
            if [ "$status" = "running" ]; then
                print_success "$service: 运行中"
            else
                print_error "$service: $status"
                all_healthy=false
            fi
        else
            print_error "$service: 未找到"
            all_healthy=false
        fi
    done
    
    echo ""
    
    if [ "$all_healthy" = true ]; then
        print_success "所有服务健康 ✨"
        return 0
    else
        print_warning "部分服务异常，请检查日志"
        return 1
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                     🎉 部署成功！🎉                         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📱 前端应用:${NC}"
    echo -e "   ${GREEN}http://localhost:3000${NC}"
    echo ""
    echo -e "${BLUE}🔧 后端 API:${NC}"
    echo -e "   ${GREEN}http://localhost:8000${NC}"
    echo -e "   API 文档: ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${BLUE}🗄️  数据库管理:${NC}"
    echo -e "   PostgreSQL: localhost:5432"
    echo -e "   用户名: ${YELLOW}postgres${NC}"
    echo -e "   密码: 查看 .env 文件中的 POSTGRES_PASSWORD"
    echo ""
    echo -e "${BLUE}🎯 向量数据库:${NC}"
    echo -e "   Milvus: localhost:19530"
    echo -e "   MinIO Console: ${GREEN}http://localhost:9001${NC}"
    echo ""
    echo -e "${BLUE}📊 常用命令:${NC}"
    echo -e "   查看日志: ${YELLOW}./deploy.sh --logs${NC}"
    echo -e "   停止服务: ${YELLOW}./deploy.sh --stop${NC}"
    echo -e "   重新部署: ${YELLOW}./deploy.sh --clean${NC}"
    echo ""
    echo -e "${BLUE}💡 提示:${NC}"
    echo -e "   首次使用请访问前端应用，创建管理员账号"
    echo ""
}

# 查看日志
show_logs() {
    print_info "显示服务日志..."
    echo ""
    print_info "按 Ctrl+C 退出日志查看"
    echo ""
    
    if docker compose version &> /dev/null; then
        docker compose logs -f --tail=100
    else
        docker-compose logs -f --tail=100
    fi
}

# 主函数
main() {
    print_header
    
    # 解析命令行参数
    case "${1:-}" in
        --clean)
            check_requirements
            check_env_file
            clean_data
            deploy_services
            wait_for_services
            health_check
            show_access_info
            ;;
        --logs)
            show_logs
            ;;
        --stop)
            stop_services
            ;;
        --health)
            health_check
            ;;
        --help)
            echo "用法: ./deploy.sh [选项]"
            echo ""
            echo "选项:"
            echo "  (无参数)    完整部署（默认）"
            echo "  --clean     清理数据并重新部署"
            echo "  --logs      查看服务日志"
            echo "  --stop      停止所有服务"
            echo "  --health    健康检查"
            echo "  --help      显示此帮助信息"
            echo ""
            ;;
        *)
            check_requirements
            check_env_file
            deploy_services
            wait_for_services
            if health_check; then
                show_access_info
            else
                print_warning "服务启动完成，但健康检查发现问题"
                print_info "请运行以下命令查看日志:"
                print_info "  ./deploy.sh --logs"
            fi
            ;;
    esac
}

# 执行主函数
main "$@"
