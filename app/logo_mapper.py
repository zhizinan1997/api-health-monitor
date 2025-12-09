"""
自动Logo匹配模块
使用中国CDN链接提供模型Logo
"""

# Logo映射表 - 使用用户提供的CDN链接
LOGO_MAP = {
    # Google Gemini
    'gemini': 'https://data.zhizinan.top/icons/gemini-color.svg',
    'bard': 'https://data.zhizinan.top/icons/gemini-color.svg',
    
    # Anthropic Claude
    'claude': 'https://data.zhizinan.top/icons/claude-color.svg',
    
    # Alibaba Qwen (通义千问)
    'qwen': 'https://data.zhizinan.top/icons/qwen-color.svg',
    '通义': 'https://data.zhizinan.top/icons/qwen-color.svg',
    
    # MiniMax
    'minimax': 'https://data.zhizinan.top/icons/minimax-color.svg',
    
    # Zhipu GLM (智谱)
    'glm': 'https://data.zhizinan.top/icons/zhipu.svg',
    'zhipu': 'https://data.zhizinan.top/icons/zhipu.svg',
    '智谱': 'https://data.zhizinan.top/icons/zhipu.svg',
    'chatglm': 'https://data.zhizinan.top/icons/zhipu.svg',
    
    # DeepSeek
    'deepseek': 'https://data.zhizinan.top/icons/deepseek-color.svg',
    
    # OpenAI GPT
    'gpt': 'https://data.zhizinan.top/icons/openai.svg',
    'chatgpt': 'https://data.zhizinan.top/icons/openai.svg',
    'davinci': 'https://data.zhizinan.top/icons/openai.svg',
    'openai': 'https://data.zhizinan.top/icons/openai.svg',
    
    # Moonshot KIMI
    'kimi': 'https://data.zhizinan.top/icons/moonshot.svg',
    'moonshot': 'https://data.zhizinan.top/icons/moonshot.svg',
    
    # xAI Grok
    'grok': 'https://data.zhizinan.top/icons/grok.svg',
    
    # 默认图标（如果都不匹配）
    'default': 'https://data.zhizinan.top/icons/openai.svg',
}

def get_logo_url(model_id: str, display_name: str = None) -> str:
    """
    根据模型ID或显示名称自动匹配Logo URL
    
    Args:
        model_id: 模型ID（如 "gpt-4", "claude-3-opus"）
        display_name: 模型显示名称（可选）
        
    Returns:
        Logo URL，如果没有匹配则返回默认图标
    """
    # 合并model_id和display_name进行搜索
    search_text = f"{model_id} {display_name or ''}".lower()
    
    # 按优先级匹配（从最具体到最通用）
    for keyword, logo_url in LOGO_MAP.items():
        if keyword == 'default':
            continue
        if keyword in search_text:
            return logo_url
    
    # 返回默认图标
    return LOGO_MAP['default']
