"""健康监控路由"""

from fastapi import APIRouter, Response, status

from src.api.schemas import HealthCheckDetail, ComponentHealth
from src.utils.health import (
    check_mysql_connection,
    check_disk_space,
    check_redis_connection,
    get_current_timestamp
)

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthCheckDetail)
async def health_check(response: Response):
    """
    功能健康监控接口
    
    深度探测后端依赖的健康状态,包括:
    - **数据库**: MySQL 连接状态
    - **磁盘空间**: 剩余空间检查 (>10%)
    - **Redis**: 如果配置了则检查连接状态
    
    ## 返回状态码
    - **200 OK**: 所有组件正常
    - **503 Service Unavailable**: 任一组件失败
    
    ## 响应格式
    ```json
    {
        "result": "succeed",  // 或 "fail"
        "timestamp": "2026-02-10T16:05:00Z",
        "details": {
            "database": {"result": "succeed", "message": "..."},
            "disk": {"result": "succeed", "details": {...}},
            "redis": {"result": "succeed", "message": "..."}  // 可选
        }
    }
    ```
    """
    # 检查所有组件
    db_result = await check_mysql_connection()
    disk_result = await check_disk_space()
    redis_result = await check_redis_connection()
    
    # 转换为 Pydantic 模型
    db_health = ComponentHealth(**db_result)
    disk_health = ComponentHealth(**disk_result)
    
    # 构建详细信息
    details = {
        "database": db_health,
        "disk": disk_health
    }
    
    # 如果配置了 Redis,添加到检查结果
    if redis_result is not None:
        redis_health = ComponentHealth(**redis_result)
        details["redis"] = redis_health
    
    # 判断总体状态
    all_systems_go = all(
        component.result == "succeed" 
        for component in details.values()
    )
    
    # 设置响应状态码
    if not all_systems_go:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return HealthCheckDetail(
        result="succeed" if all_systems_go else "fail",
        timestamp=get_current_timestamp(),
        details=details
    )
