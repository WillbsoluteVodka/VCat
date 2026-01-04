# VCat 🐱

## Description
This project is a customizable desktop pet application where users can choose a virtual pet that moves randomly across the screen, switches between different poses, and interacts with the OS in fun and engaging ways. Features include feeding, interaction with the environment, and customizable settings for a unique user experience.

---

## 🐾 猫咪行为逻辑 (Cat Behaviors)

| 行为 | 英文 | 描述 |
|------|------|------|
| 睡觉 | Sleeping | 猫咪进入休息状态 |
| 走路 | Walking | 猫咪在桌面上随机移动 |
| 坐着 | Sitting | 猫咪静坐等待互动 |
| 玩耍 | Playing | 猫咪与环境或用户互动 |
| 对话 | Coding | 猫咪打开终端/文本编辑器与用户交流 |

---

## ✨ 功能特性 (Features)

### 1. 传送门 (Portal)
- **房间系统**: 通过 Room ID + User ID 连接
- **房主机制**: 第一个创建房间的人成为房间主

### 2. 位置控制
- **菜单栏模式**: 猫咪可以移动到菜单栏
- **主屏幕模式**: 通过 Menu Bar 控制猫咪回到桌面

### 3. 购物与喂食
- 商店出售宠物食物、玩具、魔法物品
- 宠物食物可以恢复饥饿值

### 4. 外观设置
- 猫咪大小调整 (Size 变大/变小)
- 猫咪样式更换 (皮肤切换)

### 5. 网络配置
- 支持本地网络连接
- 实现跨设备宠物访问

---

## 📋 TODO 开发计划

### 高优先级
- [ ] **引导教程** - 新用户入门指引
- [ ] **拖拽小猫 / 猫窝** - 可拖拽交互 (ld)
- [ ] **菜单栏显示问题** - 修复部分系统看不到菜单栏的 Bug
- [ ] **传送门 UI + 测试 Refine** - 优化传送门界面和稳定性

### 中优先级
- [ ] **多种小猫样式** - 寻找画师/尝试 AI 生成更多皮肤
- [ ] **购物+喂食逻辑** - 完善商店系统
- [ ] **对话功能改进** - Coding 功能改为对话框，而非启动 TextEdit
  - 可能需要新的 UI 或其他实现方式

### 传送门房间功能扩展
- [ ] **打架系统** - 血量条 + 小游戏
- [ ] **贴贴功能** - 增加好感度
- [ ] 更多互动玩法...

### 🚀 Future Plan
- [ ] **Agent 功能** - 语音或双击小猫开启 Agent，可控制 Desktop/Chrome 或虚拟环境 Sandbox

---

## 💰 商业模式 (Business Model)

### 免费层 (Free Tier)
- 基础功能（走动、基本互动）

### 付费层 (Premium Tier)
- **传送门功能** - 需要数据库支持
- **官方小猫皮肤** - 需要网站支持登录注册
- **官方 Agent 功能** - 高级 AI 交互

---

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
