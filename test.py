from typing import List


def trap(height: List[int]) -> int:
    ans = 0
    last_left_max = height[0]
    last_right_max = max(height[1:])
    for i in range(1, len(height) - 1):
        left = max(last_left_max, height[i - 1])  # 当前左边最高
        last_left_max = left
        # 当前右边最高
        if height[i] < last_right_max:
            right = last_right_max
        else:
            right = max(height[i + 1:])
            last_right_max = right
        h = min(left, right)
        ans += h - height[i] if h > height[i] else 0
    return ans

print(trap([0,1,0,2,1,0,1,3,2,1,2,1]))
