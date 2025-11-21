"""
Configuration Management
Завантаження та валідація конфігурації з config.yaml та .env
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


# Завантаження .env файлу
load_dotenv()


class DatabaseConfig(BaseModel):
    """Конфігурація бази даних"""
    type: str = "sqlite"
    path: str = "data/web_assistant.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class SeleniumOptions(BaseModel):
    """Опції Selenium"""
    disable_images: bool = False
    disable_javascript: bool = False
    disable_notifications: bool = True
    disable_popup: bool = True
    incognito: bool = False


class WindowSize(BaseModel):
    """Розмір вікна браузера"""
    width: int = 1920
    height: int = 1080


class SeleniumConfig(BaseModel):
    """Конфігурація Selenium"""
    browser: str = "chrome"
    headless: bool = False
    implicit_wait: int = 10
    page_load_timeout: int = 30
    window_size: WindowSize = Field(default_factory=WindowSize)
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    download_dir: str = "downloads"
    options: SeleniumOptions = Field(default_factory=SeleniumOptions)


class LMStudioConfig(BaseModel):
    """Конфігурація LM Studio"""
    base_url: str = "http://localhost:1234/v1"
    model: str = "local-model"
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 60


class OllamaConfig(BaseModel):
    """Конфігурація Ollama"""
    base_url: str = "http://localhost:11434"
    model: str = "llama2"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 60


class PromptsConfig(BaseModel):
    """Шаблони промптів"""
    system: str = "Ти асистент для аналізу веб-контенту."
    analyze_text: str = "Проаналізуй текст..."
    summarize: str = "Створи резюме..."
    extract_info: str = "Витягни інформацію..."


class LLMConfig(BaseModel):
    """Конфігурація LLM"""
    provider: str = "lm_studio"
    lm_studio: LMStudioConfig = Field(default_factory=LMStudioConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)


class CacheConfig(BaseModel):
    """Конфігурація кешування"""
    enabled: bool = True
    max_size: int = 1000
    ttl: int = 86400
    use_hash: bool = True
    hash_algorithm: str = "md5"


class ModeConfig(BaseModel):
    """Конфігурація режиму"""
    enabled: bool = True
    selectors: List[str] = Field(default_factory=list)
    min_text_length: Optional[int] = None
    suggest_selectors: Optional[bool] = None
    confirm_before_extract: Optional[bool] = None
    show_devtools: Optional[bool] = None


class ModesConfig(BaseModel):
    """Конфігурація режимів роботи"""
    auto: ModeConfig = Field(default_factory=ModeConfig)
    semi_auto: ModeConfig = Field(default_factory=ModeConfig)
    manual: ModeConfig = Field(default_factory=ModeConfig)


class WindowConfig(BaseModel):
    """Конфігурація вікна"""
    width: int = 1600
    height: int = 900
    resizable: bool = True


class PanelConfig(BaseModel):
    """Конфігурація панелі"""
    position: str = "left"
    width: Optional[int] = None
    height: Optional[int] = None
    collapsible: Optional[bool] = None


class PanelsConfig(BaseModel):
    """Конфігурація панелей"""
    browser: PanelConfig = Field(default_factory=PanelConfig)
    results: PanelConfig = Field(default_factory=PanelConfig)
    debug: PanelConfig = Field(default_factory=PanelConfig)


class UIConfig(BaseModel):
    """Конфігурація UI"""
    theme: str = "dark"
    language: str = "uk"
    show_debug_panel: bool = True
    auto_scroll: bool = True
    syntax_highlighting: bool = True
    window: WindowConfig = Field(default_factory=WindowConfig)
    panels: PanelsConfig = Field(default_factory=PanelsConfig)


class FileLoggingConfig(BaseModel):
    """Конфігурація логування у файл"""
    enabled: bool = True
    path: str = "logs/app.log"
    max_bytes: int = 10485760
    backup_count: int = 5


class ConsoleLoggingConfig(BaseModel):
    """Конфігурація консольного логування"""
    enabled: bool = True
    colored: bool = True


class LoggerConfig(BaseModel):
    """Конфігурація окремого логера"""
    level: str = "INFO"
    file: str = "logs/default.log"


class LoggingConfig(BaseModel):
    """Конфігурація логування"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file: FileLoggingConfig = Field(default_factory=FileLoggingConfig)
    console: ConsoleLoggingConfig = Field(default_factory=ConsoleLoggingConfig)
    loggers: Dict[str, LoggerConfig] = Field(default_factory=dict)


class PerformanceConfig(BaseModel):
    """Конфігурація продуктивності"""
    max_concurrent_tasks: int = 3
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1


class SecurityConfig(BaseModel):
    """Конфігурація безпеки"""
    allowed_domains: List[str] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)
    max_text_length: int = 50000
    sanitize_input: bool = True


class ExportConfig(BaseModel):
    """Конфігурація експорту"""
    formats: List[str] = Field(default_factory=lambda: ["json", "csv", "txt"])
    default_format: str = "json"
    directory: str = "exports"
    include_metadata: bool = True


class AppConfig(BaseModel):
    """Головна конфігурація застосунку"""
    name: str = "Web Assistant"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"


class Settings(BaseModel):
    """Головний клас налаштувань"""
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    selenium: SeleniumConfig = Field(default_factory=SeleniumConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    modes: ModesConfig = Field(default_factory=ModesConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)

    @classmethod
    def load_from_yaml(cls, config_path: str = "config.yaml") -> "Settings":
        """
        Завантаження конфігурації з YAML файлу
        
        Args:
            config_path: Шлях до файлу конфігурації
            
        Returns:
            Settings: Об'єкт налаштувань
        """
        if not os.path.exists(config_path):
            print(f"[WARNING] Config file not found: {config_path}, using defaults")
            return cls()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                config_data = {}
            
            return cls(**config_data)
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}, using defaults")
            return cls()
    
    def save_to_yaml(self, config_path: str = "config.yaml") -> None:
        """
        Збереження конфігурації у YAML файл
        
        Args:
            config_path: Шлях до файлу конфігурації
        """
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, allow_unicode=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Отримання значення за ключем з підтримкою точкової нотації
        
        Args:
            key: Ключ у форматі "section.subsection.value"
            default: Значення за замовчуванням
            
        Returns:
            Any: Значення або default
        """
        keys = key.split('.')
        value = self.model_dump()
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value


# Singleton instance
_settings: Optional[Settings] = None


def get_settings(reload: bool = False) -> Settings:
    """
    Отримання глобального екземпляру налаштувань (singleton)
    
    Args:
        reload: Перезавантажити конфігурацію
        
    Returns:
        Settings: Об'єкт налаштувань
    """
    global _settings
    
    if _settings is None or reload:
        _settings = Settings.load_from_yaml()
    
    return _settings


# Для зручності
settings = get_settings()