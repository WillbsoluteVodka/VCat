# DesktopPet

## Description
This project is a customizable desktop pet application where users can choose a virtual pet that moves randomly across the screen, switches between different poses, and interacts with the OS in fun and engaging ways. Features include feeding, interaction with the environment, and customizable settings for a unique user experience.

## Installation
Follow these steps to install and run the application:

### 方法一：使用启动脚本（推荐）

1. 确保已安装 Python 3.8 或更高版本
2. 在项目根目录下运行：
```bash
./run.sh
```

启动脚本会自动：
- 创建虚拟环境（如果不存在）
- 安装所需依赖
- 启动应用程序

### 方法二：手动安装

1. 创建虚拟环境：
```bash
python3 -m venv venv
```

2. 激活虚拟环境：
```bash
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 运行应用：
```bash
PYTHONPATH=$(pwd) python src/main_window.py
```

### 依赖说明
- PyQt5 >= 5.15.0 (GUI 框架)
- pyobjc-framework-Cocoa >= 9.0 (macOS 工具栏功能)

## Progress Checklist

- [X] Basic features
  - A pet that can randomly move on the desktop
  - At least three poses that it will switch from time to time
- [X] Feed pets and pets’ hunger/life feature
  - [ ] Optionally, include a growing process for each pet
- [ ] Ultimate shop
  - [X] The shop will sell three kinds of things: pet food, pet toy, magical things
  - [X] Improved shop UI with new background and styled item cards
  - [X] Pet food will heal the pet and get them out of hungry mode
  - [ ] Pet toy can be used to interact with the pet in different ways
  - [ ] Magical things
    - [ ] A drag sign that can drag your pet into your menu bar, the cat will stay there walk and rest until you release it using this item
- [ ] Pets’ interaction with the OS and the user
  - [X] Open and type some command into the terminal
  - [X] Open a .txt file and write things to it
    - [ ] Add more text options including pictures maybe
  - [ ] Chase and steal the mouse
  - [ ] If ignored too long, make noises or stain the screen
  - [ ] Disturb the pet with mouse while it's sleeping/sitting
  - [X] To achieve the effect of "petting a cat" by continuously moving the mouse over the cat's body, the cat will transition from a sitting posture to lying down and showing its belly.
  - [ ] Potential interaction with different frame or background color
- [ ] Selection interface
  - User can select their eggs, with each egg generating a pet
  - [X] Acts as a settings bar for adjusting basic appearance of the pets
- [ ] Custom pet creation
  - Users can upload or create their own pets using this toolbar
- [ ] Pet travel
  - [X] User's pet can travel to their friends' desktops under some conditions(such as connecting to the same network and both running the app)
  - [ ] On their friend's desk top, the friend can feed other user's pets and the pet will store the states it obtained when getting back
  - [ ] On a friend's desktop, two pets will randomly have two situation: hate each other (be on guard), where they will be angry when they are close to each other like fried hair look
  - [ ] Or like each other where they will play hide and seek with each other using the tabs opened on the screen
