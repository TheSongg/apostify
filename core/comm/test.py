import redis
import os

r = redis.Redis(host='127.0.0.1', port=6379, password=os.getenv('REDIS_PASSWORD'))

# 匹配所有以 'failed_queue:' 开头的任务队列
match_pattern = '*'
keys_to_delete = []

# 使用 scan_iter 安全地迭代所有匹配的键
for key in r.scan_iter(match_pattern):
    keys_to_delete.append(key)

if keys_to_delete:
    # 批量删除找到的所有键
    r.delete(*keys_to_delete)
    print(f"成功删除了 {len(keys_to_delete)} 个匹配的任务队列。")
else:
    print("未找到匹配的任务队列。")