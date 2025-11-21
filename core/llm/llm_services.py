"""
LLM Base Client and LM Studio Implementation
Базовий клас для LLM та реалізація для LM Studio
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import time
import requests
from requests.exceptions import RequestException, Timeout
from .base import BaseLLMClient
from ..config.settings import get_settings
from ..utils.logger import get_logger
from ..utils.exceptions import LLMError


logger = get_logger(__name__)


# ==================== LM STUDIO CLIENT ====================

class LMStudioClient(BaseLLMClient):
    """
    Клієнт для LM Studio
    Підтримує OpenAI-сумісний API
    """
    
    def __init__(self):
        """Ініціалізація LM Studio клієнта"""
        super().__init__()
        
        self.base_url = self.settings.llm.lm_studio.base_url
        self.model = self.settings.llm.lm_studio.model
        self.default_temperature = self.settings.llm.lm_studio.temperature
        self.default_max_tokens = self.settings.llm.lm_studio.max_tokens
        self.timeout = self.settings.llm.lm_studio.timeout
        
        # Endpoints
        self.chat_endpoint = f"{self.base_url}/chat/completions"
        self.models_endpoint = f"{self.base_url}/models"
        
        logger.info(f"LM Studio client initialized: {self.base_url}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Генерація відповіді через LM Studio
        
        Args:
            prompt: Промпт користувача
            system_prompt: Системний промпт
            temperature: Температура (0.0 - 2.0)
            max_tokens: Максимум токенів
            **kwargs: stream, top_p, frequency_penalty, presence_penalty
            
        Returns:
            Dict: {'response', 'tokens_used', 'processing_time', 'model'}
        """
        start_time = time.time()
        
        # Підготовка повідомлень
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Параметри запиту
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.default_temperature,
            "max_tokens": max_tokens or self.default_max_tokens,
            "stream": kwargs.get("stream", False)
        }
        
        # Додаткові параметри
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        if "frequency_penalty" in kwargs:
            payload["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            payload["presence_penalty"] = kwargs["presence_penalty"]
        
        try:
            logger.debug(f"Sending request to LM Studio: {payload}")
            
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            processing_time = time.time() - start_time
            
            # Парсинг відповіді
            result = {
                "response": data["choices"][0]["message"]["content"],
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                "processing_time": processing_time,
                "model": data.get("model", self.model),
                "finish_reason": data["choices"][0].get("finish_reason", "stop")
            }
            
            logger.info(
                f"LM Studio response received: {result['tokens_used']} tokens, "
                f"{processing_time:.2f}s"
            )
            
            return result
            
        except Timeout:
            error_msg = f"LM Studio request timeout after {self.timeout}s"
            logger.error(error_msg)
            raise LLMError(error_msg)
            
        except RequestException as e:
            error_msg = f"LM Studio request failed: {e}"
            logger.error(error_msg)
            raise LLMError(error_msg)
            
        except KeyError as e:
            error_msg = f"Invalid LM Studio response format: {e}"
            logger.error(error_msg)
            raise LLMError(error_msg)
    
    def is_available(self) -> bool:
        """
        Перевірка доступності LM Studio сервера
        
        Returns:
            bool: True якщо сервер доступний
        """
        try:
            response = requests.get(
                self.models_endpoint,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("LM Studio server is available")
                return True
            else:
                logger.warning(f"LM Studio returned status {response.status_code}")
                return False
                
        except RequestException as e:
            logger.error(f"LM Studio server unavailable: {e}")
            return False
    
    def list_models(self) -> list:
        """
        Список доступних моделей
        
        Returns:
            list: Список моделей
        """
        try:
            response = requests.get(
                self.models_endpoint,
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            models = [model["id"] for model in data.get("data", [])]
            
            logger.info(f"Available models: {models}")
            return models
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def analyze_text(
        self,
        text: str,
        url: str,
        selector: str
    ) -> str:
        """
        Аналіз тексту з веб-сторінки
        
        Args:
            text: Текст для аналізу
            url: URL сторінки
            selector: Селектор елемента
            
        Returns:
            str: Результат аналізу
        """
        prompt_template = self.settings.llm.prompts.analyze_text
        prompt = self.format_prompt(
            prompt_template,
            text=text,
            url=url,
            selector=selector
        )
        
        system_prompt = self.settings.llm.prompts.system
        
        result = self.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        return result["response"]
    
    def summarize_text(self, text: str) -> str:
        """
        Створення резюме тексту
        
        Args:
            text: Текст для резюмування
            
        Returns:
            str: Резюме
        """
        prompt_template = self.settings.llm.prompts.summarize
        prompt = self.format_prompt(prompt_template, text=text)
        
        result = self.generate(prompt=prompt)
        return result["response"]
    
    def extract_information(self, text: str) -> str:
        """
        Витягування ключової інформації
        
        Args:
            text: Текст для обробки
            
        Returns:
            str: Витягнута інформація
        """
        prompt_template = self.settings.llm.prompts.extract_info
        prompt = self.format_prompt(prompt_template, text=text)
        
        result = self.generate(prompt=prompt)
        return result["response"]


# ==================== OLLAMA CLIENT ====================

class OllamaClient(BaseLLMClient):
    """
    Клієнт для Ollama
    """
    
    def __init__(self):
        """Ініціалізація Ollama клієнта"""
        super().__init__()
        
        self.base_url = self.settings.llm.ollama.base_url
        self.model = self.settings.llm.ollama.model
        self.default_temperature = self.settings.llm.ollama.temperature
        self.default_max_tokens = self.settings.llm.ollama.max_tokens
        self.timeout = self.settings.llm.ollama.timeout
        
        # Endpoints
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.chat_endpoint = f"{self.base_url}/api/chat"
        self.tags_endpoint = f"{self.base_url}/api/tags"
        
        logger.info(f"Ollama client initialized: {self.base_url}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Генерація відповіді через Ollama"""
        start_time = time.time()
        
        # Ollama використовує chat API
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.default_temperature,
                "num_predict": max_tokens or self.default_max_tokens
            }
        }
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            processing_time = time.time() - start_time
            
            result = {
                "response": data["message"]["content"],
                "tokens_used": data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
                "processing_time": processing_time,
                "model": data.get("model", self.model),
                "finish_reason": "stop"
            }
            
            logger.info(f"Ollama response: {result['tokens_used']} tokens, {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            raise LLMError(f"Ollama error: {e}")
    
    def is_available(self) -> bool:
        """Перевірка доступності Ollama"""
        try:
            response = requests.get(self.tags_endpoint, timeout=5)
            return response.status_code == 200
        except Exception:
            return False


# ==================== FACTORY ====================

def create_llm_client(provider: Optional[str] = None) -> BaseLLMClient:
    """
    Фабрика для створення LLM клієнта
    
    Args:
        provider: Провайдер (lm_studio, ollama) або None для конфігу
        
    Returns:
        BaseLLMClient: Клієнт LLM
    """
    settings = get_settings()
    provider = provider or settings.llm.provider
    
    if provider == "lm_studio":
        return LMStudioClient()
    elif provider == "ollama":
        return OllamaClient()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")