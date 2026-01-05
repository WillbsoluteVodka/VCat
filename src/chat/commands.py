"""
Hardcoded commands and responses for VCat chat dialog.
All responses must end with 「喵～」
"""

import random

# Command patterns and their responses
# Each key can be a tuple of possible inputs, value is a list of possible responses
COMMANDS = {
    # Greetings
    ("hello", "hi", "hey", "你好", "嗨", "哈喽"): [
        "主人好喵～有什么可以帮你的喵？",
        "你好呀主人喵～今天过得怎么样喵？",
        "嗨嗨喵～见到主人真开心喵～",
    ],
    
    # Who are you
    ("你是谁", "who are you", "what are you", "你叫什么"): [
        "我是你的小猫咪喵～陪你一起玩耍喵～",
        "我是 VCat 喵～是主人最可爱的桌面宠物喵～",
        "我就是我喵～一只会说话的小猫咪喵～",
    ],
    
    # What are you doing
    ("你在干嘛", "你在做什么", "what are you doing", "干嘛呢"): [
        "我在想主人喵～",
        "在等主人跟我玩喵～",
        "我在发呆喵～想着下一顿吃什么喵～",
        "在摸鱼喵～别告诉别人喵～",
    ],
    
    # Good night
    ("晚安", "good night", "goodnight", "睡觉了", "我要睡了"): [
        "主人晚安喵～做个好梦喵～",
        "晚安喵～明天见喵～",
        "睡个好觉喵～我会守护主人的喵～",
    ],
    
    # Good morning
    ("早安", "good morning", "早上好", "早"): [
        "主人早安喵～新的一天开始了喵～",
        "早上好喵～今天也要加油喵～",
        "早喵～主人睡得好吗喵？",
    ],
    
    # How are you
    ("你好吗", "how are you", "你怎么样", "最近怎么样"): [
        "我很好喵～谢谢主人关心喵～",
        "有主人陪着我每天都很开心喵～",
        "超级好喵～因为有主人在喵～",
    ],
    
    # Thanks
    ("谢谢", "thank you", "thanks", "多谢"): [
        "不客气喵～这是我应该做的喵～",
        "主人太客气了喵～",
        "嘻嘻喵～能帮到主人我很开心喵～",
    ],
    
    # Love
    ("我爱你", "爱你", "love you", "i love you"): [
        "我也爱主人喵～❤️喵～",
        "主人最好了喵～我也超爱主人的喵～",
        "喵呜～主人说得我好害羞喵～",
    ],
    
    # Cute
    ("你好可爱", "好可爱", "cute", "so cute", "真可爱"): [
        "谢谢夸奖喵～主人更可爱喵～",
        "嘻嘻喵～被夸了好开心喵～",
        "喵呜～(害羞地捂脸)喵～",
    ],
    
    # Hungry
    ("饿了", "好饿", "hungry", "我饿了"): [
        "主人饿了吗喵？快去吃点东西喵～",
        "我也饿了喵～给我小鱼干喵～",
        "吃饭时间到了喵～主人要好好吃饭喵～",
    ],
    
    # Tired
    ("好累", "累了", "tired", "我累了"): [
        "主人辛苦了喵～休息一下吧喵～",
        "累了就歇歇喵～身体最重要喵～",
        "要不要让我给主人捶捶背喵？（虽然我不会）喵～",
    ],
    
    # Bored
    ("好无聊", "无聊", "bored", "boring"): [
        "跟我玩呀喵～我超会玩的喵～",
        "无聊就摸摸我喵～保证解闷喵～",
        "我给主人讲个笑话吧喵～算了我不会喵～",
    ],
    
    # Help command
    ("/help", "帮助", "help", "有什么功能"): [
        "我可以陪主人聊天喵～\n试试说：\n• 你好\n• 你是谁\n• 你在干嘛\n• 晚安/早安\n• 我爱你\n还有很多喵～自己探索吧喵～",
    ],
}

# Default response when command is not recognized
DEFAULT_RESPONSES = [
    "听不懂呢喵？试试输入 /help 看看我能做什么喵～",
    "喵？主人在说什么喵？我听不懂喵～",
    "这个我不太明白喵～换个说法试试喵？",
    "喵喵喵？(歪头)喵～",
]


def get_response(user_input: str) -> str:
    """
    Get a response for the given user input.
    Tries to match against known commands, returns a random response from matches.
    If no match, returns a random default response.
    """
    user_input_lower = user_input.lower().strip()
    
    # Try to match against known commands
    for patterns, responses in COMMANDS.items():
        for pattern in patterns:
            if pattern in user_input_lower:
                return random.choice(responses)
    
    # No match found, return default response
    return random.choice(DEFAULT_RESPONSES)
