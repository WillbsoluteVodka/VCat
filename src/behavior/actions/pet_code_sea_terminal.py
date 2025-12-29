import time
import random
import os


fish_frames_right = [
    r"><(((°>",
    r"><)))))°>",
    r"><))°>",
    r"><))))°>"
]

fish_frames_left = [
    r"<°)))><",
    r"<°)))))><",
    r"<°))><",
    r"<°))))><"
]


tre_frames_right = [
    r" /\           ",
    r"( /   @ @    ()",
    r" \  __| |__  / ",
    r"  -/   \"   \- ",
    r" /-|       |-\ ",
    r"/ /-\     /-\ \\",
    r" / /-`---'-\ \  ",
    r"  /         \   "
]

tre_frames_left = [
    r"           /\  ",
    r"()    @ @   \ )",
    r" \  __| |__  / ",
    r"  -/   \"   \- ",
    r" /-|       |-\ ",
    r"/ /-\     /-\ \\",
    r" / /-`---'-\ \  ",
    r"  /         \   "
]


new_creature_right = [
    r"     |\    o",
    r"    |  \    o",
    r"|\ /    .\ o",
    r"| |       (",
    r"|/ \     /",
    r"    |  /",
    r"     |/"
]

new_creature_left = [
    r"o    /|     ",
    r"o   /  |    ",
    r"o /.    \  /|",
    r" )       |  |",
    r"   \     / \| ",
    r"    \   /      ",
    r"     \ |       "
]


blue = "\033[94m"  # 蓝色
green = "\033[92m"  # 绿色
reset = "\033[0m"  # 重置颜色



def clear():
    os.system("clear" if os.name == "posix" else "cls")



def animal_swim_animation():
    width = os.get_terminal_size().columns  # 获取终端宽度

    fish_positions = [random.randint(0, width // 2) for _ in range(5)]  # 每条鱼的初始位置
    fish_directions = [random.choice([1, -1]) for _ in range(5)]  # 每条鱼的方向
    fish_speeds = [random.randint(1, 2) for _ in range(5)]  # 每条鱼的速度 (越小越快)
    fish_counters = [0] * 5  # 控制每条鱼的速度

    tre_position = random.randint(0, width // 2)  # Tre 的初始位置
    tre_direction = random.choice([1, -1])  # Tre 的方向

    new_creature_position = random.randint(0, width // 2)  # New Creature 的初始位置
    new_creature_direction = random.choice([1, -1])  # New Creature 的方向

    try:
        while True:
            clear()

            # 动态生成彩色水面和装饰物
            water_waves = "".join(
                random.choice([blue + "~" + reset, " ", green + reset, blue + "~" + reset])
                for _ in range(width)
            )
            print(water_waves)  # 打印水面

            # 显示多条鱼
            for i in range(5):
                if fish_directions[i] == 1:  # 向右游动
                    fish = fish_frames_right[i % len(fish_frames_right)]
                else:  # 向左游动
                    fish = fish_frames_left[i % len(fish_frames_left)]

                print(" " * fish_positions[i] + fish)

                # 控制更新频率
                fish_counters[i] += 1
                if fish_counters[i] >= fish_speeds[i]:
                    fish_positions[i] += fish_directions[i]
                    fish_counters[i] = 0  # 重置计数器

                # 更新方向
                if fish_positions[i] >= width - len(fish):  # 碰到右边界
                    fish_directions[i] = -1
                elif fish_positions[i] <= 0:  # 碰到左边界
                    fish_directions[i] = 1

            # 显示 "Tre"
            if tre_direction == 1:  # 向右移动
                tre = "\n".join(
                    " " * tre_position + line
                    for line in tre_frames_right
                )
            else:  # 向左移动
                tre = "\n".join(
                    " " * tre_position + line
                    for line in tre_frames_left
                )

            print(tre)

            # 更新 "Tre" 的位置和方向
            tre_position += tre_direction
            if tre_position >= width - max(len(line) for line in tre_frames_right):  # 碰到右边界
                tre_direction = -1
            elif tre_position <= 0:  # 碰到左边界
                tre_direction = 1

            # 显示 New Creature
            if new_creature_direction == 1:  # 向右移动
                creature = "\n".join(
                    " " * new_creature_position + line
                    for line in new_creature_right
                )
            else:  # 向左移动
                creature = "\n".join(
                    " " * new_creature_position + line
                    for line in new_creature_left
                )

            print(creature)

            # 更新 New Creature 的位置和方向
            new_creature_position += new_creature_direction
            if new_creature_position >= width - max(len(line) for line in new_creature_right):  # 碰到右边界
                new_creature_direction = -1
            elif new_creature_position <= 0:  # 碰到左边界
                new_creature_direction = 1

            time.sleep(0.1)
    except KeyboardInterrupt:
        clear()
        print("Cat like fish!")


# 主函数
if __name__ == "__main__":
    animal_swim_animation()
