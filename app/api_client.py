"""
OpenAI API client for testing model connectivity
"""
import httpx
from typing import Optional, List, Tuple
from app.logger import log_debug


def normalize_base_url(api_base_url: str) -> str:
    """
    Normalize API base URL to ensure consistent format.
    Removes trailing slashes and /v1, /v1/chat/completions etc.
    Returns base URL like: https://api.example.com
    """
    url = api_base_url.strip().rstrip("/")
    
    # Remove common suffixes
    suffixes = ["/v1/chat/completions", "/v1/models", "/v1"]
    for suffix in suffixes:
        if url.lower().endswith(suffix.lower()):
            url = url[:-len(suffix)]
    
    return url.rstrip("/")


async def get_available_models(api_base_url: str, api_key: str) -> Tuple[bool, List[dict], Optional[str]]:
    """
    Fetch available models from the API using OpenAI format
    
    Returns:
        Tuple of (success, models_list, error_message)
    """
    if not api_base_url or not api_key:
        return False, [], "API 地址或密钥未配置"
    
    # Normalize URL and build models endpoint
    base_url = normalize_base_url(api_base_url)
    url = f"{base_url}/v1/models"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        log_debug("INFO", "api_client", f"正在获取模型列表: {url}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                log_debug("INFO", "api_client", f"成功获取 {len(models)} 个模型")
                return True, models, None
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                log_debug("ERROR", "api_client", f"获取模型失败: {error_msg}")
                return False, [], error_msg
                
    except httpx.TimeoutException:
        error_msg = "请求超时"
        log_debug("ERROR", "api_client", f"从 {url} 获取模型超时")
        return False, [], error_msg
    except httpx.ConnectError as e:
        error_msg = f"连接失败: {str(e)[:100]}"
        log_debug("ERROR", "api_client", f"连接错误: {e}")
        return False, [], error_msg
    except Exception as e:
        error_msg = f"未知错误: {str(e)[:100]}"
        log_debug("ERROR", "api_client", f"获取模型时出错: {e}")
        return False, [], error_msg


async def test_model_connectivity(
    api_base_url: str, 
    api_key: str, 
    model_id: str
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Test model connectivity by sending a simple chat request
    
    Returns:
        Tuple of (success, error_code, error_message)
        - success: True if model responded successfully
        - error_code: HTTP status code or custom error code (None if success)
        - error_message: Brief error description (None if success)
    """
    if not api_base_url or not api_key:
        return False, 0, "API未配置"
    
    # Normalize URL and build chat endpoint
    base_url = normalize_base_url(api_base_url)
    url = f"{base_url}/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_id,
        "messages": [
            {"role": "user", "content": "hi"}
        ],
        "max_tokens": 10,
        "temperature": 0
    }
    
    try:
        log_debug("INFO", "api_client", f"测试模型 {model_id} 连通性")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                # Check if we got a valid response with choices
                if "choices" in data and len(data["choices"]) > 0:
                    log_debug("INFO", "api_client", f"模型 {model_id} 测试成功")
                    return True, None, None
                else:
                    log_debug("WARNING", "api_client", f"模型 {model_id} 返回空响应")
                    return False, 200, "空响应"
            else:
                # Try to extract error message from response
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", {}).get("message", response.text[:100])
                except:
                    error_detail = response.text[:100]
                
                error_msg = _get_brief_error_message(response.status_code, error_detail)
                log_debug("ERROR", "api_client", f"模型 {model_id} 测试失败: {response.status_code} - {error_detail}")
                return False, response.status_code, error_msg
                
    except httpx.TimeoutException:
        log_debug("ERROR", "api_client", f"模型 {model_id} 测试超时")
        return False, 408, "请求超时 (60秒)"
    except httpx.ConnectError:
        log_debug("ERROR", "api_client", f"模型 {model_id} 连接失败")
        return False, 503, "连接失败"
    except Exception as e:
        log_debug("ERROR", "api_client", f"模型 {model_id} 测试错误: {e}")
        return False, 500, f"错误: {str(e)[:50]}"


def _get_brief_error_message(status_code: int, detail: str) -> str:
    """Get a brief, user-friendly error message in Chinese"""
    error_messages = {
        400: "请求错误",
        401: "认证失败",
        403: "拒绝访问",
        404: "模型未找到",
        429: "频率限制",
        500: "服务器错误",
        502: "网关错误",
        503: "服务不可用",
        504: "网关超时"
    }
    
    base_msg = error_messages.get(status_code, f"HTTP {status_code}")
    
    # Add brief detail if useful
    if detail and len(detail) < 50:
        return f"{base_msg}: {detail}"
    return base_msg
