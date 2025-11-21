"""
Selenium Browser Wrapper
Обгортка для WebDriver з підтримкою різних браузерів
"""

from typing import Optional, List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService

from ..config.settings import get_settings
from ..utils.logger import get_logger
from ..utils.exceptions import BrowserError


logger = get_logger(__name__)


class SeleniumBrowser:
    """
    Обгортка для Selenium WebDriver
    Підтримує Chrome, Firefox, Edge з автоматичним встановленням драйверів
    """
    
    def __init__(self, browser_type: Optional[str] = None, headless: Optional[bool] = None):
        """
        Ініціалізація браузера
        
        Args:
            browser_type: Тип браузера (chrome, firefox, edge)
            headless: Headless режим
        """
        self.settings = get_settings()
        self.browser_type = browser_type or self.settings.selenium.browser
        self.headless = headless if headless is not None else self.settings.selenium.headless
        
        self.driver: Optional[webdriver.Remote] = None
        self._initialize_driver()
    
    def _initialize_driver(self) -> None:
        """Ініціалізація WebDriver"""
        try:
            if self.browser_type.lower() == "chrome":
                self.driver = self._create_chrome_driver()
            elif self.browser_type.lower() == "firefox":
                self.driver = self._create_firefox_driver()
            elif self.browser_type.lower() == "edge":
                self.driver = self._create_edge_driver()
            else:
                raise BrowserError(f"Unsupported browser: {self.browser_type}")
            
            # Налаштування таймаутів
            self.driver.implicitly_wait(self.settings.selenium.implicit_wait)
            self.driver.set_page_load_timeout(self.settings.selenium.page_load_timeout)
            
            # Розмір вікна
            width = self.settings.selenium.window_size.width
            height = self.settings.selenium.window_size.height
            self.driver.set_window_size(width, height)
            
            logger.info(f"Browser initialized: {self.browser_type}, headless={self.headless}")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise BrowserError(f"Browser initialization failed: {e}")
    
    def _create_chrome_driver(self) -> webdriver.Chrome:
        """Створення Chrome WebDriver"""
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        # Базові опції
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Опції з конфігу
        if self.settings.selenium.options.disable_images:
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
        
        if self.settings.selenium.options.disable_notifications:
            options.add_argument("--disable-notifications")
        
        if self.settings.selenium.options.incognito:
            options.add_argument("--incognito")
        
        if self.settings.selenium.user_agent:
            options.add_argument(f"user-agent={self.settings.selenium.user_agent}")
        
        if self.settings.selenium.proxy:
            options.add_argument(f"--proxy-server={self.settings.selenium.proxy}")
        
        # Директорія завантажень
        if self.settings.selenium.download_dir:
            prefs = {
                "download.default_directory": self.settings.selenium.download_dir,
                "download.prompt_for_download": False
            }
            options.add_experimental_option("prefs", prefs)
        
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    
    def _create_firefox_driver(self) -> webdriver.Firefox:
        """Створення Firefox WebDriver"""
        options = webdriver.FirefoxOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        if self.settings.selenium.options.incognito:
            options.add_argument("-private")
        
        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=options)
    
    def _create_edge_driver(self) -> webdriver.Edge:
        """Створення Edge WebDriver"""
        options = webdriver.EdgeOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        if self.settings.selenium.options.incognito:
            options.add_argument("--inprivate")
        
        service = EdgeService(EdgeChromiumDriverManager().install())
        return webdriver.Edge(service=service, options=options)
    
    def navigate_to(self, url: str) -> bool:
        """
        Перехід на URL
        
        Args:
            url: URL сторінки
            
        Returns:
            bool: True якщо успішно
        """
        try:
            self.driver.get(url)
            logger.info(f"Navigated to: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return False
    
    def find_element(
        self,
        selector: str,
        by: By = By.CSS_SELECTOR,
        timeout: int = 10
    ) -> Optional[WebElement]:
        """
        Знаходження елемента
        
        Args:
            selector: Селектор елемента
            by: Тип селектора
            timeout: Таймаут очікування
            
        Returns:
            WebElement або None
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            logger.warning(f"Element not found: {selector}")
            return None
        except Exception as e:
            logger.error(f"Error finding element {selector}: {e}")
            return None
    
    def find_elements(
        self,
        selector: str,
        by: By = By.CSS_SELECTOR
    ) -> List[WebElement]:
        """
        Знаходження кількох елементів
        
        Args:
            selector: Селектор
            by: Тип селектора
            
        Returns:
            List[WebElement]: Список елементів
        """
        try:
            return self.driver.find_elements(by, selector)
        except Exception as e:
            logger.error(f"Error finding elements {selector}: {e}")
            return []
    
    def get_element_text(
        self,
        selector: str,
        by: By = By.CSS_SELECTOR
    ) -> Optional[str]:
        """
        Отримання тексту елемента
        
        Args:
            selector: Селектор
            by: Тип селектора
            
        Returns:
            str: Текст елемента або None
        """
        element = self.find_element(selector, by)
        if element:
            return element.text
        return None
    
    def execute_script(self, script: str, *args) -> Any:
        """
        Виконання JavaScript
        
        Args:
            script: JavaScript код
            *args: Аргументи для скрипта
            
        Returns:
            Any: Результат виконання
        """
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return None
    
    def highlight_element(
        self,
        element: WebElement,
        color: str = "red",
        duration: int = 2
    ) -> None:
        """
        Підсвічування елемента на сторінці
        
        Args:
            element: WebElement для підсвічування
            color: Колір підсвітки
            duration: Тривалість у секундах
        """
        original_style = element.get_attribute("style")
        
        self.execute_script(
            f"arguments[0].style.border = '3px solid {color}';",
            element
        )
        
        # Відновлення оригінального стилю через duration секунд
        import time
        time.sleep(duration)
        
        self.execute_script(
            f"arguments[0].setAttribute('style', '{original_style}');",
            element
        )
    
    def take_screenshot(self, filename: str) -> bool:
        """
        Створення скріншоту
        
        Args:
            filename: Ім'я файлу
            
        Returns:
            bool: True якщо успішно
        """
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return False
    
    def get_page_source(self) -> str:
        """Отримання HTML коду сторінки"""
        return self.driver.page_source
    
    def get_current_url(self) -> str:
        """Отримання поточного URL"""
        return self.driver.current_url
    
    def get_page_title(self) -> str:
        """Отримання заголовку сторінки"""
        return self.driver.title
    
    def refresh(self) -> None:
        """Оновлення сторінки"""
        self.driver.refresh()
        logger.info("Page refreshed")
    
    def back(self) -> None:
        """Повернутися назад"""
        self.driver.back()
    
    def forward(self) -> None:
        """Вперед"""
        self.driver.forward()
    
    def close(self) -> None:
        """Закриття поточної вкладки"""
        if self.driver:
            self.driver.close()
    
    def quit(self) -> None:
        """Закриття браузера"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.quit()