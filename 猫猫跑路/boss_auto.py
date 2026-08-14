import time
import random
import threading
from datetime import datetime
from typing import Callable, Optional


class BossAutoApply:
    def __init__(self, log_callback: Optional[Callable] = None):
        self.driver = None
        self.log_callback = log_callback
        self.is_running = False
        self.is_paused = False
        self.applied_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.job_list = []
        self.login_success = False

    def _log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {msg}"
        if self.log_callback:
            self.log_callback(log_msg)
        print(log_msg)

    def _random_sleep(self, min_sec=1, max_sec=3):
        time.sleep(random.uniform(min_sec, max_sec))

    def init_driver(self):
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                use_manager = True
            except ImportError:
                use_manager = False
        except ImportError:
            raise ImportError("请安装依赖: pip install selenium webdriver-manager")

        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1400,900')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        self._log("正在初始化浏览器...")
        try:
            if use_manager:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
            self._log("浏览器初始化成功")
            return True
        except Exception as e:
            self._log(f"浏览器初始化失败: {e}")
            return False

    def open_login_page(self):
        if not self.driver:
            self._log("请先初始化浏览器")
            return False
        try:
            self._log("正在打开BOSS直聘登录页面，请使用手机APP扫码登录...")
            self.driver.get("https://login.zhipin.com/")
            self._log("请在3分钟内完成扫码登录")
            return True
        except Exception as e:
            self._log(f"打开登录页失败: {e}")
            return False

    def wait_for_login(self, timeout=180) -> bool:
        if not self.driver:
            return False
        self._log("等待登录中...请扫码")
        start = time.time()
        while time.time() - start < timeout:
            try:
                current_url = self.driver.current_url
                if "zhipin.com/web/geek" in current_url or current_url == "https://www.zhipin.com/web/geek/job":
                    self.login_success = True
                    self._log("登录成功！")
                    return True
                if "login" not in current_url and current_url != "about:blank":
                    self.login_success = True
                    self._log(f"登录成功！当前页面: {current_url}")
                    return True
            except:
                pass
            time.sleep(2)
        self._log("登录超时")
        return False

    def search_jobs(self, keyword: str, city: str = "101010100", page: int = 1):
        if not self.driver or not self.login_success:
            self._log("请先登录")
            return []

        self._log(f"正在搜索岗位: 关键词={keyword}, 城市代码={city}, 第{page}页")
        city_map = {
            "北京": "101010100",
            "上海": "101020100",
            "广州": "101280100",
            "深圳": "101280600",
            "杭州": "101210100",
            "成都": "101270100",
            "武汉": "101200100",
            "西安": "101110100",
            "南京": "101190100",
            "重庆": "101040100",
            "天津": "101030100",
            "苏州": "101190400",
            "长沙": "101250100",
            "郑州": "101180100",
            "青岛": "101120200",
            "全国": "100010000",
        }
        if city in city_map:
            city_code = city_map[city]
        else:
            city_code = city

        search_url = f"https://www.zhipin.com/web/geek/job?query={keyword}&city={city_code}&page={page}"
        try:
            self.driver.get(search_url)
            self._random_sleep(3, 5)
            jobs = self._parse_job_list()
            self._log(f"找到 {len(jobs)} 个岗位")
            return jobs
        except Exception as e:
            self._log(f"搜索岗位失败: {e}")
            return []

    def _parse_job_list(self):
        if not self.driver:
            return []
        try:
            from selenium.webdriver.common.by import By
            jobs = []
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-card-wrapper, .search-job-result li, li.job-card-box")
            self._log(f"找到 {len(job_cards)} 个岗位卡片")
            for idx, card in enumerate(job_cards):
                try:
                    job = {}
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, ".job-name, .job-title, [class*='title']")
                        job['title'] = title_elem.text.strip()
                    except:
                        continue
                    try:
                        company_elem = card.find_element(By.CSS_SELECTOR, ".company-name, [class*='company']")
                        job['company'] = company_elem.text.strip()
                    except:
                        job['company'] = "未知"
                    try:
                        salary_elem = card.find_element(By.CSS_SELECTOR, ".salary, [class*='salary']")
                        job['salary'] = salary_elem.text.strip()
                    except:
                        job['salary'] = "面议"
                    try:
                        job['link'] = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except:
                        job['link'] = ""
                    try:
                        area_elem = card.find_element(By.CSS_SELECTOR, ".job-area, [class*='area'], [class*='city']")
                        job['area'] = area_elem.text.strip()
                    except:
                        job['area'] = ""
                    job['id'] = idx
                    jobs.append(job)
                except:
                    continue
            return jobs
        except Exception as e:
            self._log(f"解析岗位列表失败: {e}")
            return []

    def get_job_list(self):
        return self.job_list

    def apply_job(self, job_url: str) -> int:
        if not self.driver or not self.login_success:
            self._log("请先登录")
            return -1
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            self._log(f"正在打开岗位页面: {job_url[:80]}...")
            self.driver.get(job_url)
            self._random_sleep(3, 5)

            try:
                apply_btn_selectors = [
                    ".btn.btn-startchat",
                    ".job-operate .btn",
                    "[class*='chat-btn']",
                    "[class*='apply-btn']",
                    "//button[contains(text(), '立即沟通')]",
                    "//button[contains(text(), '投递简历')]",
                    "//a[contains(text(), '立即沟通')]",
                    "//a[contains(text(), '投递简历')]",
                ]

                apply_btn = None
                for selector in apply_btn_selectors:
                    try:
                        if selector.startswith("//"):
                            btn = self.driver.find_element(By.XPATH, selector)
                        else:
                            btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if btn and btn.is_displayed() and btn.is_enabled():
                            apply_btn = btn
                            break
                    except:
                        continue

                if not apply_btn:
                    self._log("未找到投递按钮，可能已投递过或岗位不匹配")
                    self.skipped_count += 1
                    return 1

                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_btn)
                    self._random_sleep(1, 2)
                    self.driver.execute_script("arguments[0].click();", apply_btn)
                    self._random_sleep(2, 4)

                    try:
                        confirm_selectors = [
                            "//button[contains(text(), '确定')]",
                            "//button[contains(text(), '发送')]",
                            "//button[contains(text(), '确认')]",
                            ".confirm-btn",
                            ".sure-btn",
                        ]
                        for sel in confirm_selectors:
                            try:
                                if sel.startswith("//"):
                                    confirm = self.driver.find_element(By.XPATH, sel)
                                else:
                                    confirm = self.driver.find_element(By.CSS_SELECTOR, sel)
                                if confirm.is_displayed():
                                    self.driver.execute_script("arguments[0].click();", confirm)
                                    self._random_sleep(1, 2)
                                    break
                            except:
                                continue
                    except:
                        pass

                    self.applied_count += 1
                    self._log(f"投递成功！已投递: {self.applied_count} 个岗位")
                    return 0

                except Exception as ce:
                    self._log(f"点击投递按钮失败: {ce}")
                    self.failed_count += 1
                    return -1

            except Exception as be:
                self._log(f"查找投递按钮失败: {be}")
                self.failed_count += 1
                return -1

        except Exception as e:
            self._log(f"投递过程出错: {e}")
            self.failed_count += 1
            return -1

    def start_auto_apply(self, keyword: str, city: str = "北京",
                         max_pages: int = 3, max_applies: int = 20,
                         delay_min: int = 5, delay_max: int = 15):
        if self.is_running:
            self._log("已有任务在运行中")
            return

        def _run():
            self.is_running = True
            self.is_paused = False
            self._log(f"========== 开始自动投递 ==========")
            self._log(f"关键词: {keyword} | 城市: {city}")
            self._log(f"最多搜索页数: {max_pages} | 最多投递数: {max_applies}")

            try:
                for page in range(1, max_pages + 1):
                    if not self.is_running:
                        break
                    if self.applied_count >= max_applies:
                        self._log(f"已达到最大投递数 {max_applies}，结束")
                        break

                    while self.is_paused and self.is_running:
                        time.sleep(1)
                        continue
                    if not self.is_running:
                        break

                    jobs = self.search_jobs(keyword, city, page)
                    if not jobs:
                        self._log(f"第{page}页无岗位，继续下一页")
                        continue

                    for job in jobs:
                        if not self.is_running:
                            break
                        if self.applied_count >= max_applies:
                            break

                        while self.is_paused and self.is_running:
                            time.sleep(1)
                            continue
                        if not self.is_running:
                            break

                        self._log(f"\n处理岗位: [{job.get('title', '')}] @ {job.get('company', '')} | {job.get('salary', '')}")
                        if job.get('link'):
                            self.apply_job(job['link'])
                        else:
                            self.skipped_count += 1

                        delay = random.randint(delay_min, delay_max)
                        self._log(f"等待 {delay} 秒后继续...")
                        for i in range(delay):
                            if not self.is_running:
                                break
                            while self.is_paused and self.is_running:
                                time.sleep(1)
                            time.sleep(1)

            except Exception as e:
                self._log(f"自动投递异常: {e}")
            finally:
                self.is_running = False
                self._log(f"========== 投递结束 ==========")
                self._log(f"统计: 成功投递={self.applied_count}, 失败={self.failed_count}, 跳过={self.skipped_count}")

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def pause(self):
        self.is_paused = True
        self._log("已暂停")

    def resume(self):
        self.is_paused = False
        self._log("已继续")

    def stop(self):
        self.is_running = False
        self.is_paused = False
        self._log("正在停止...")

    def reset_count(self):
        self.applied_count = 0
        self.failed_count = 0
        self.skipped_count = 0

    def close(self):
        self.is_running = False
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.login_success = False
                self._log("浏览器已关闭")
            except:
                pass

    def get_status(self):
        return {
            'running': self.is_running,
            'paused': self.is_paused,
            'applied': self.applied_count,
            'failed': self.failed_count,
            'skipped': self.skipped_count,
            'login': self.login_success,
        }
