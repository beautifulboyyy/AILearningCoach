from collections import defaultdict


def lengthOfLongestSubstring(s: str) -> int:
    count = defaultdict(int)
    ans = 0
    left = 0
    for right, num in enumerate(s):
        # 右边进
        if not num in count:
            count[num] += 1
            ans = max(ans, len(count))
            continue
        # 当前num在count里，left移动找到相同的出来
        while left < right and num in count:
            count[s[left]] -= 1
            if count[s[left]] == 0: count.pop(s[left])
            left += 1
        # 当前num进去
        count[num] += 1
    return ans

print(lengthOfLongestSubstring(" "))