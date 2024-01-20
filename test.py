from datetime import datetime, timedelta

# 将时间字符串转换为datetime对象
start_time_str = "2024-01-15T00:00:00+08:00"
end_time_str = "2024-01-18T00:30:00+08:00"

start_time = datetime.fromisoformat(start_time_str)
end_time = datetime.fromisoformat(end_time_str)

# 逐天迭代
current_time = start_time
while current_time < end_time:
    next_day = current_time + timedelta(days=1)
    # 转换为ISO格式的字符串
    start_time_iso = current_time.isoformat()
    end_time_iso = next_day.isoformat()

    if end_time_iso > end_time_str:
        end_time_iso = end_time_str


    # 这里是每天调用API的代码
    # 例如: call_api(start_time_iso, end_time_iso)
    print(f"调用API：开始时间 {start_time_iso}, 结束时间 {end_time_iso}")

    # 到下一天
    current_time = next_day


keys = ['a', 'b', 'a', 'c']
values = [1, 2, 3, 4]

mapped_dict = dict(zip(keys, values))
print(mapped_dict)
