height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
n = len(height)

# 1. 初始化记录数组，长度与 height 相同，初始值全为 0
# 这个数组将存储每个位置“右侧”的最大值
right_max_record = [0] * n

# 2. 维护一个变量，记录当前遍历过的右侧最大值
# 初始化为 0，因为最右边的元素右侧没有东西，最大值视为 0
current_max = 0

# 3. 从右向左遍历 (索引从 n-1 到 0)
# 注意：我们要计算的是位置 i 的“右边”最大值，所以在处理 i 时，
# current_max 存储的是 i+1 到末尾的最大值。
for i in range(n - 1, -1, -1):
    # 步骤 A: 先记录当前位置的结果
    # 此时 current_max 正好是 height[i+1:] 的最大值
    right_max_record[i] = current_max

    # 步骤 B: 更新 current_max，把当前位置的值纳入考量，供下一次循环（i-1）使用
    if height[i] > current_max:
        current_max = height[i]

# 输出结果验证
print(f"原始高度: {height}")
print(f"右侧最大: {right_max_record}")

# 打印详细对照表
print("\n详细对照 (索引 | 高度 | 右侧最大值):")
for i in range(n):
    print(f"idx {i}: height={height[i]}, right_max={right_max_record[i]}")