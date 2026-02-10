"""
独立测试健康检查功能
不依赖完整应用启动
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# 直接导入健康检查函数
from src.utils.health import (
    check_mysql_connection,
    check_disk_space,
    check_redis_connection,
    get_current_timestamp
)


async def test_health_checks():
    """测试所有健康检查功能"""
    print("=" * 60)
    print("健康检查功能测试")
    print("=" * 60)
    
    # 1. 测试数据库连接
    print("\n1. 测试 MySQL 数据库连接...")
    db_health = await check_mysql_connection()
    print(f"   结果: {db_health['result']}")
    print(f"   消息: {db_health.get('message', 'N/A')}")
    if db_health.get('details'):
        print(f"   详情: {db_health['details']}")
    
    # 2. 测试磁盘空间
    print("\n2. 测试磁盘空间...")
    disk_health = await check_disk_space()
    print(f"   结果: {disk_health['result']}")
    print(f"   消息: {disk_health.get('message', 'N/A')}")
    if disk_health.get('details'):
        print(f"   详情: {disk_health['details']}")
    
    # 3. 测试 Redis 连接 (可选)
    print("\n3. 测试 Redis 连接...")
    redis_health = await check_redis_connection()
    if redis_health:
        print(f"   结果: {redis_health['result']}")
        print(f"   消息: {redis_health.get('message', 'N/A')}")
    else:
        print("   跳过 (未配置 Redis)")
    
    # 4. 测试时间戳生成
    print("\n4. 测试时间戳生成...")
    timestamp = get_current_timestamp()
    print(f"   时间戳: {timestamp}")
    
    # 5. 汇总结果
    print("\n" + "=" * 60)
    print("汇总结果")
    print("=" * 60)
    
    components = {
        "database": db_health,
        "disk": disk_health
    }
    if redis_health:
        components["redis"] = redis_health
    
    all_ok = all(c['result'] == "succeed" for c in components.values())
    
    print(f"\n总体状态: {'✅ 成功' if all_ok else '❌ 失败'}")
    print(f"时间戳: {timestamp}")
    print("\n组件详情:")
    for name, health in components.items():
        status_icon = "✅" if health['result'] == "succeed" else "❌"
        print(f"  {status_icon} {name}: {health['result']}")
    
    print("\n" + "=" * 60)
    
    # 模拟 API 响应
    print("\n模拟 API 响应 JSON:")
    result_str = "succeed" if all_ok else "fail"
    print("{")
    print(f'  "result": "{result_str}",')
    print(f'  "timestamp": "{timestamp}",')
    print('  "details": {')
    for i, (name, health) in enumerate(components.items()):
        comma = "," if i < len(components) - 1 else ""
        print(f'    "{name}": {{')
        print(f'      "result": "{health["result"]}",')
        msg = health.get('message', '')
        print(f'      "message": "{msg}"')
        print(f'    }}{comma}')
    print('  }')
    print("}")
    
    # 返回状态码
    status_code = 200 if all_ok else 503
    print(f"\nHTTP 状态码: {status_code}")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_health_checks())
    sys.exit(exit_code)
