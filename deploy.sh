#!/bin/bash

# MCP服务部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}开始部署MCP服务...${NC}"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose未安装${NC}"
    exit 1
fi

# 创建必要的目录
echo -e "${YELLOW}创建目录结构...${NC}"
mkdir -p logs data monitoring/dashboards

# 检查环境文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}警告: .env文件不存在，从.example复制${NC}"
    cp .env.example .env
    echo -e "${YELLOW}请编辑.env文件设置配置${NC}"
fi

# 构建镜像
echo -e "${YELLOW}构建Docker镜像...${NC}"
docker-compose build

# 启动服务
echo -e "${YELLOW}启动服务...${NC}"
docker-compose up -d

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo -e "${GREEN}检查服务状态...${NC}"
docker-compose ps

# 健康检查
echo -e "${YELLOW}执行健康检查...${NC}"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MCP服务运行正常${NC}"
else
    echo -e "${RED}✗ MCP服务健康检查失败${NC}"
    echo -e "${YELLOW}查看日志: docker-compose logs image-utils-mcp${NC}"
    exit 1
fi

echo -e "${GREEN}部署完成！${NC}"
echo -e "访问以下地址："
echo -e "- MCP服务API: http://localhost:8000"
echo -e "- API文档: http://localhost:8000/docs"
echo -e "- Prometheus: http://localhost:9090"
echo -e "- Grafana: http://localhost:3000"
echo -e ""
echo -e "管理命令："
echo -e "  查看日志: docker-compose logs -f"
echo -e "  停止服务: docker-compose down"
echo -e "  重启服务: docker-compose restart"