import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from resume_parser import ResumeParser
from boss_auto import BossAutoApply


def _res_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


# 粉色女性向配色板
PALETTE = {
    "bg_cream":       "#FFF5F8",   # 主背景 - 奶粉
    "bg_card":        "#FFF0F5",   # 卡片 - 樱花粉
    "bg_card_alt":    "#FFE4EC",   # 强调卡片 - 豆沙粉
    "bg_drop":        "#FFE4EC",   # 拖放区 - 淡粉
    "bg_drop_border": "#FFB6C1",   # 拖放区边框
    "bg_log":         "#FFF8FA",   # 日志 - 乳粉

    "fg_main":        "#5D4E6D",   # 正文 - 紫灰
    "fg_sub":         "#8B7A99",   # 次要文字
    "fg_hint":        "#B8A5C4",   # 提示文字
    "fg_white":       "#FFFFFF",   # 反白

    "primary":        "#FF6B9D",   # 主按钮 - 玫瑰粉
    "primary_dark":   "#E85587",   # 主按钮按下
    "primary_hover":  "#FF85B1",
    "success":        "#7BC47F",   # 成功 - 粉嫩绿
    "warning":        "#E8A87C",   # 警告 - 蜜桃橙
    "danger":         "#E06C75",   # 错误 - 粉红
    "info":           "#9B8BA7",   # 普通信息 - 紫灰
    "accent_amber":   "#FFC0CB",   # 点缀 - 粉
    "divider":        "#FFD6E0",   # 分隔线
}


class JobApp:
    def __init__(self, root):
        self.root = root
        self.root.title("猫猫跑路 · BOSS直聘自动投递")
        self.root.geometry("1120x800")
        self.root.minsize(980, 720)
        self.root.configure(bg=PALETTE["bg_cream"])

        self._load_assets()
        self._set_window_icon()

        self.resume_parser = ResumeParser()
        self.boss = BossAutoApply(log_callback=self._append_log)
        self.resume_data = None
        self.resume_file_path = ""

        self._setup_style()
        self._build_ui()
        self._update_status_loop()

    def _load_assets(self):
        self._logo_tk = None
        self._logo_small_tk = None
        self._header_tk = None

        if not PIL_AVAILABLE:
            return

        assets = {
            "logo":   _res_path("assets/logo_circle.png"),
            "banner": _res_path("assets/header_banner_final.png"),
        }

        try:
            if os.path.exists(assets["logo"]):
                logo = Image.open(assets["logo"]).convert("RGBA")
                self._logo_img = logo.resize((40, 40), Image.LANCZOS)
                self._logo_tk = ImageTk.PhotoImage(self._logo_img)
                sm = logo.resize((28, 28), Image.LANCZOS)
                self._logo_small_img = sm
                self._logo_small_tk = ImageTk.PhotoImage(sm)
        except Exception as e:
            print("加载logo失败:", e)

        try:
            if os.path.exists(assets["banner"]):
                banner = Image.open(assets["banner"]).convert("RGB")
                self._header_img = banner
                self._header_tk = ImageTk.PhotoImage(banner)
        except Exception as e:
            print("加载横幅失败:", e)

    def _set_window_icon(self):
        if not PIL_AVAILABLE:
            return
        for cand in [_res_path("assets/app.ico"),
                     _res_path("assets/logo_circle.png")]:
            if not os.path.exists(cand):
                continue
            try:
                if cand.lower().endswith(".ico"):
                    self.root.iconbitmap(default=cand)
                else:
                    img = Image.open(cand)
                    tkimg = ImageTk.PhotoImage(img)
                    self.root.iconphoto(True, tkimg)
                    self._window_icon_ref = tkimg
                break
            except Exception as e:
                print("设置窗口图标失败:", e)

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass

        P = PALETTE
        style.configure('.', background=P["bg_cream"], foreground=P["fg_main"],
                        font=('Microsoft YaHei UI', 10))

        style.configure('Title.TLabel',
                        font=('Microsoft YaHei UI', 18, 'bold'),
                        foreground=P["primary_dark"],
                        background=P["bg_cream"])
        style.configure('SubTitle.TLabel',
                        font=('Microsoft YaHei UI', 11, 'bold'),
                        foreground=P["fg_main"],
                        background=P["bg_card"])
        style.configure('Hint.TLabel',
                        font=('Microsoft YaHei UI', 9),
                        foreground=P["fg_hint"],
                        background=P["bg_card"])
        style.configure('HintOnCream.TLabel',
                        font=('Microsoft YaHei UI', 9),
                        foreground=P["fg_hint"],
                        background=P["bg_cream"])
        style.configure('Slogan.TLabel',
                        font=('Microsoft YaHei UI', 10, 'italic'),
                        foreground=P["primary_dark"],
                        background=P["bg_cream"])
        style.configure('Success.TLabel',
                        font=('Microsoft YaHei UI', 9, 'bold'),
                        foreground=P["success"], background=P["bg_card"])
        style.configure('Warning.TLabel',
                        font=('Microsoft YaHei UI', 9, 'bold'),
                        foreground=P["warning"], background=P["bg_card"])
        style.configure('Danger.TLabel',
                        font=('Microsoft YaHei UI', 9, 'bold'),
                        foreground=P["danger"], background=P["bg_card"])

        style.configure('Card.TFrame',
                        background=P["bg_card"], relief='solid',
                        borderwidth=1, bordercolor=P["divider"])

        style.configure('Primary.TButton',
                        font=('Microsoft YaHei UI', 10, 'bold'),
                        foreground=P["fg_white"],
                        background=P["primary"],
                        padding=(14, 8), borderwidth=0)
        style.map('Primary.TButton',
                  background=[('active', P["primary_hover"]),
                              ('pressed', P["primary_dark"]),
                              ('disabled', '#E8D5DB')],
                  foreground=[('disabled', '#FFF5F8')])

        style.configure('Secondary.TButton',
                        font=('Microsoft YaHei UI', 9),
                        foreground=P["fg_main"],
                        background=P["bg_card_alt"],
                        padding=(10, 5), borderwidth=1)
        style.map('Secondary.TButton',
                  background=[('active', '#FFD6E0')])

        style.configure('TEntry',
                        fieldbackground='#FFFFFF',
                        foreground=P["fg_main"],
                        bordercolor=P["divider"],
                        lightcolor=P["divider"], darkcolor=P["divider"])
        style.configure('TCombobox',
                        fieldbackground='#FFFFFF',
                        background='#FFFFFF',
                        foreground=P["fg_main"])
        style.configure('TSpinbox',
                        fieldbackground='#FFFFFF',
                        foreground=P["fg_main"])

        style.configure('TSeparator', background=P["divider"])
        style.configure('TPanedwindow', background=P["bg_cream"])

    def _build_ui(self):
        self._build_header_banner()

        main_frame = ttk.Frame(self.root, padding=(14, 10, 14, 14))
        main_frame.pack(fill=tk.BOTH, expand=True)

        content = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True)

        left_outer = ttk.Frame(content, padding=6)
        right_panel = ttk.Frame(content, padding=6)
        content.add(left_outer, weight=3)
        content.add(right_panel, weight=4)

        canvas = tk.Canvas(left_outer, bg=PALETTE["bg_cream"],
                           highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(left_outer, orient=tk.VERTICAL,
                                  command=canvas.yview)
        left_panel = tk.Frame(canvas, bg=PALETTE["bg_cream"])
        left_panel.bind('<Configure>',
                        lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        left_panel_window = canvas.create_window((0, 0), window=left_panel, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind('<Configure>',
                    lambda e: canvas.itemconfigure(left_panel_window, width=e.width))

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind_all('<MouseWheel>', _on_mousewheel)
        canvas.bind('<Enter>', lambda e: canvas.bind_all('<MouseWheel>', _on_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))

        self._build_resume_section(left_panel)
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        self._build_login_section(left_panel)
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        self._build_config_section(left_panel)

        self._build_control_section(right_panel)
        ttk.Separator(right_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        self._build_log_section(right_panel)

    def _build_header_banner(self):
        if self._header_tk:
            banner_wrap = tk.Frame(self.root, bg=PALETTE["bg_cream"], height=110)
            banner_wrap.pack(fill=tk.X)
            banner_wrap.pack_propagate(False)

            banner_lbl = tk.Label(banner_wrap,
                                  image=self._header_tk,
                                  bg=PALETTE["bg_cream"],
                                  bd=0, highlightthickness=0, anchor='e')
            banner_lbl.place(x=0, y=0, relwidth=1, height=110)

            title_frame = tk.Frame(banner_wrap, bg=PALETTE["bg_cream"])
            title_frame.place(x=24, y=18)

            row1 = tk.Frame(title_frame, bg=PALETTE["bg_cream"])
            row1.pack(anchor=tk.W)
            if self._logo_tk:
                tk.Label(row1, image=self._logo_tk,
                         bg=PALETTE["bg_cream"], bd=0).pack(side=tk.LEFT, padx=(0, 12))
            tk.Label(row1,
                     text="猫猫跑路",
                     font=('Microsoft YaHei UI', 20, 'bold'),
                     fg=PALETTE["primary_dark"],
                     bg=PALETTE["bg_cream"]).pack(side=tk.LEFT, pady=(4, 0))

            tk.Label(title_frame,
                     text="拜拜了！提起小桶去投新简历  🐱  简历解析 → BOSS直聘自动投递",
                     font=('Microsoft YaHei UI', 10),
                     fg=PALETTE["fg_sub"],
                     bg=PALETTE["bg_cream"]).pack(anchor=tk.W, pady=(6, 0), padx=2)
        else:
            header = ttk.Frame(self.root, padding=(14, 10))
            header.pack(fill=tk.X)
            ttk.Label(header, text="🐱  猫猫跑路", style='Title.TLabel').pack(side=tk.LEFT)
            ttk.Label(header, text="  简历解析 + BOSS直聘自动投递",
                      style='HintOnCream.TLabel').pack(side=tk.LEFT, pady=(8, 0))

    def _section_head(self, parent, title_text, status_lbl=None):
        head = tk.Frame(parent, bg=PALETTE["bg_card"])
        head.pack(fill=tk.X)
        if self._logo_small_tk:
            tk.Label(head, image=self._logo_small_tk,
                     bg=PALETTE["bg_card"], bd=0).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(head, text=title_text, style='SubTitle.TLabel').pack(side=tk.LEFT)
        if status_lbl is not None:
            status_lbl.pack(side=tk.RIGHT)
        return head

    def _build_resume_section(self, parent):
        card = tk.Frame(parent, bg=PALETTE["bg_card"],
                        highlightthickness=1,
                        highlightbackground=PALETTE["divider"],
                        padx=12, pady=12)
        card.pack(fill=tk.X)

        self.resume_status_lbl = ttk.Label(card, text="未上传", style='Warning.TLabel')
        self._section_head(card, "📄  简历上传与解析", self.resume_status_lbl)

        drop_frame = tk.Frame(card, bg=PALETTE["bg_drop"], height=52,
                              highlightthickness=1,
                              highlightbackground=PALETTE["bg_drop_border"])
        drop_frame.pack(fill=tk.X, pady=(8, 4))
        drop_frame.pack_propagate(False)
        drop_frame.bind('<Button-1>', lambda e: self._choose_resume())

        self.drop_lbl = tk.Label(drop_frame,
                                 text="📎  点击选择或拖拽简历文件 (PDF · Word · TXT)",
                                 bg=PALETTE["bg_drop"],
                                 fg=PALETTE["primary_dark"],
                                 font=('Microsoft YaHei UI', 9, 'bold'),
                                 cursor='hand2',
                                 justify=tk.CENTER)
        self.drop_lbl.pack(expand=True, fill=tk.BOTH)
        self.drop_lbl.bind('<Button-1>', lambda e: self._choose_resume())

        if DND_AVAILABLE:
            try:
                for w in (drop_frame, self.drop_lbl):
                    w.drop_target_register(DND_FILES)
                    w.dnd_bind('<<Drop>>', self._on_drop)
            except:
                pass

        btn_row = tk.Frame(card, bg=PALETTE["bg_card"])
        btn_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(btn_row, text="选择简历文件",
                   style='Primary.TButton', command=self._choose_resume).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="重新解析",
                   style='Secondary.TButton', command=self._reparse_resume).pack(side=tk.LEFT, padx=8)

        info_frame = tk.Frame(card, bg=PALETTE["bg_card"])
        info_frame.pack(fill=tk.X, pady=(8, 0))

        def add_field(label, *, bold=False, color=None):
            row = tk.Frame(info_frame, bg=PALETTE["bg_card"])
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, width=7, anchor=tk.W,
                     fg=PALETTE["fg_hint"], bg=PALETTE["bg_card"],
                     font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT)
            value = tk.Label(row, text="-", anchor=tk.W, justify=tk.LEFT,
                             wraplength=300,
                             font=('Microsoft YaHei UI', 9, 'bold' if bold else 'normal'),
                             fg=color or PALETTE["fg_main"], bg=PALETTE["bg_card"])
            value.pack(side=tk.LEFT, fill=tk.X, expand=True)
            return value

        self.name_lbl = add_field("姓名:", bold=True)
        self.phone_lbl = add_field("电话:")
        self.email_lbl = add_field("邮箱:")
        self.target_lbl = add_field("期望:", bold=True, color=PALETTE["primary_dark"])

        tk.Label(info_frame, text="🎯 技能 / 关键词", anchor=tk.W,
                 fg=PALETTE["primary_dark"], bg=PALETTE["bg_card"],
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W, pady=(6, 2))
        self.skills_text = tk.Text(info_frame, height=2,
                                   bg='#FFFFFF', fg=PALETTE["fg_main"],
                                   relief='flat', bd=0,
                                   highlightthickness=1,
                                   highlightbackground=PALETTE["divider"],
                                   font=('Microsoft YaHei UI', 9), wrap=tk.WORD,
                                   padx=8, pady=4)
        self.skills_text.pack(fill=tk.X)
        self.skills_text.insert(tk.END, "解析后显示")
        self.skills_text.config(state=tk.DISABLED)

        tk.Label(info_frame, text="🎓 学历 / 教育", anchor=tk.W,
                 fg=PALETTE["primary_dark"], bg=PALETTE["bg_card"],
                 font=('Microsoft YaHei UI', 9, 'bold')).pack(anchor=tk.W, pady=(6, 2))
        self.edu_lbl = tk.Label(info_frame, text="-",
                                font=('Microsoft YaHei UI', 9),
                                fg=PALETTE["fg_main"], bg=PALETTE["bg_card"],
                                justify=tk.LEFT, anchor=tk.W, wraplength=300)
        self.edu_lbl.pack(fill=tk.X)

    def _build_login_section(self, parent):
        card = tk.Frame(parent, bg=PALETTE["bg_card"],
                        highlightthickness=1,
                        highlightbackground=PALETTE["divider"],
                        padx=12, pady=12)
        card.pack(fill=tk.X)

        self.login_status_lbl = ttk.Label(card, text="未登录", style='Warning.TLabel')
        self._section_head(card, "🔐  BOSS直聘登录", self.login_status_lbl)

        row = tk.Frame(card, bg=PALETTE["bg_card"])
        row.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(row, text="① 启动浏览器",
                   style='Primary.TButton', command=self._start_browser).pack(side=tk.LEFT)
        ttk.Button(row, text="② 打开登录页",
                   style='Secondary.TButton', command=self._open_login).pack(side=tk.LEFT, padx=8)
        ttk.Button(row, text="③ 检测登录状态",
                   style='Secondary.TButton', command=self._check_login).pack(side=tk.LEFT)
        ttk.Button(row, text="关闭浏览器",
                   style='Secondary.TButton', command=self._close_browser).pack(side=tk.RIGHT)

        tk.Label(card,
                 text="💡  BOSS直聘需要扫码登录，请在弹出的Chrome浏览器中使用BOSS直聘APP扫码。",
                 font=('Microsoft YaHei UI', 9),
                 fg=PALETTE["fg_hint"], bg=PALETTE["bg_card"],
                 anchor=tk.W, justify=tk.LEFT).pack(fill=tk.X, pady=(12, 0))

    def _build_config_section(self, parent):
        card = tk.Frame(parent, bg=PALETTE["bg_card"],
                        highlightthickness=1,
                        highlightbackground=PALETTE["divider"],
                        padx=12, pady=12)
        card.pack(fill=tk.X)
        self._section_head(card, "⚙️  搜索与投递配置")

        form = tk.Frame(card, bg=PALETTE["bg_card"])
        form.pack(fill=tk.X, pady=(12, 0))

        def grid_label(r, text):
            tk.Label(form, text=text, anchor=tk.W,
                     fg=PALETTE["fg_sub"], bg=PALETTE["bg_card"],
                     font=('Microsoft YaHei UI', 10)).grid(
                row=r, column=0, sticky=tk.W, pady=6)

        grid_label(0, "搜索关键词:")
        self.keyword_entry = ttk.Entry(form, font=('Microsoft YaHei UI', 10))
        self.keyword_entry.grid(row=0, column=1, sticky=tk.EW, pady=6, padx=8)
        ttk.Button(form, text="← 从简历获取",
                   style='Secondary.TButton', command=self._fill_from_resume).grid(row=0, column=2, pady=6)

        grid_label(1, "城        市:")
        self.city_combo = ttk.Combobox(form, values=[
            "全国", "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉",
            "西安", "南京", "重庆", "天津", "苏州", "长沙", "郑州", "青岛"
        ], state='readonly', font=('Microsoft YaHei UI', 10))
        self.city_combo.set("北京")
        self.city_combo.grid(row=1, column=1, sticky=tk.EW, pady=6, padx=8)

        grid_label(2, "搜索页数:")
        self.max_pages_spin = ttk.Spinbox(form, from_=1, to=10, width=10)
        self.max_pages_spin.set(3)
        self.max_pages_spin.grid(row=2, column=1, sticky=tk.W, pady=6, padx=8)

        grid_label(3, "最大投递数:")
        self.max_apply_spin = ttk.Spinbox(form, from_=1, to=200, width=10)
        self.max_apply_spin.set(20)
        self.max_apply_spin.grid(row=3, column=1, sticky=tk.W, pady=6, padx=8)

        grid_label(4, "投递间隔(秒):")
        delay_frame = tk.Frame(form, bg=PALETTE["bg_card"])
        delay_frame.grid(row=4, column=1, sticky=tk.W, pady=6, padx=8)
        self.delay_min = ttk.Spinbox(delay_frame, from_=2, to=60, width=6)
        self.delay_min.set(5)
        self.delay_min.pack(side=tk.LEFT)
        tk.Label(delay_frame, text=" ~ ", bg=PALETTE["bg_card"],
                 fg=PALETTE["fg_hint"]).pack(side=tk.LEFT)
        self.delay_max = ttk.Spinbox(delay_frame, from_=2, to=120, width=6)
        self.delay_max.set(15)
        self.delay_max.pack(side=tk.LEFT)

        form.columnconfigure(1, weight=1)

    def _build_control_section(self, parent):
        card = tk.Frame(parent, bg=PALETTE["bg_card"],
                        highlightthickness=1,
                        highlightbackground=PALETTE["divider"],
                        padx=12, pady=12)
        card.pack(fill=tk.X)
        self._section_head(card, "🎮  投递控制")

        stats = tk.Frame(card, bg=PALETTE["bg_card"])
        stats.pack(fill=tk.X, pady=(14, 14))

        def stat_cell(col, num_var, label, color):
            num_var.grid(row=0, column=col, padx=18)
            tk.Label(stats, text=label,
                     fg=PALETTE["fg_hint"], bg=PALETTE["bg_card"],
                     font=('Microsoft YaHei UI', 9)).grid(row=1, column=col, padx=18)

        self.applied_num = tk.Label(stats, text="0",
                                    font=('Microsoft YaHei UI', 26, 'bold'),
                                    fg=PALETTE["primary"], bg=PALETTE["bg_card"])
        self.failed_num = tk.Label(stats, text="0",
                                   font=('Microsoft YaHei UI', 26, 'bold'),
                                   fg=PALETTE["danger"], bg=PALETTE["bg_card"])
        self.skipped_num = tk.Label(stats, text="0",
                                    font=('Microsoft YaHei UI', 26, 'bold'),
                                    fg=PALETTE["warning"], bg=PALETTE["bg_card"])
        stat_cell(0, self.applied_num, "已投递", PALETTE["primary"])
        stat_cell(1, self.failed_num, "失败", PALETTE["danger"])
        stat_cell(2, self.skipped_num, "跳过", PALETTE["warning"])

        self.run_status = tk.Label(stats, text="空闲",
                                   font=('Microsoft YaHei UI', 18, 'bold'),
                                   fg=PALETTE["success"], bg=PALETTE["bg_card"])
        self.run_status.grid(row=0, column=3, rowspan=2, padx=18)

        btns = tk.Frame(card, bg=PALETTE["bg_card"])
        btns.pack(fill=tk.X)
        self.start_btn = ttk.Button(btns, text="▶ 开始自动投递",
                                    style='Primary.TButton', command=self._start_apply)
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.pause_btn = ttk.Button(btns, text="⏸ 暂停",
                                    style='Secondary.TButton',
                                    command=self._pause_apply, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.stop_btn = ttk.Button(btns, text="⏹ 停止",
                                   style='Secondary.TButton',
                                   command=self._stop_apply, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btns, text="清零", style='Secondary.TButton',
                   command=self._reset_count).pack(side=tk.LEFT, padx=(10, 0))

    def _build_log_section(self, parent):
        card = tk.Frame(parent, bg=PALETTE["bg_card"],
                        highlightthickness=1,
                        highlightbackground=PALETTE["divider"],
                        padx=12, pady=12)
        card.pack(fill=tk.BOTH, expand=True)
        head = tk.Frame(card, bg=PALETTE["bg_card"])
        head.pack(fill=tk.X)
        self._section_head(card, "📋  运行日志")
        clear_wrap = tk.Frame(card, bg=PALETTE["bg_card"])
        clear_wrap.place(relx=1.0, y=12, anchor=tk.NE)
        ttk.Button(clear_wrap, text="清空日志", style='Secondary.TButton',
                   command=self._clear_log).pack()

        self.log_text = scrolledtext.ScrolledText(
            card, wrap=tk.WORD,
            font=('Consolas', 10),
            bg=PALETTE["bg_log"],
            fg=PALETTE["fg_main"],
            insertbackground=PALETTE["primary"],
            selectbackground=PALETTE["accent_amber"],
            relief='flat', bd=0,
            highlightthickness=1,
            highlightbackground=PALETTE["divider"],
            height=14, padx=10, pady=8,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.log_text.tag_configure('tag_info', foreground=PALETTE["info"])
        self.log_text.tag_configure('tag_ok',   foreground=PALETTE["success"])
        self.log_text.tag_configure('tag_warn', foreground=PALETTE["warning"])
        self.log_text.tag_configure('tag_err',  foreground=PALETTE["danger"])

    def _append_log(self, msg):
        def _do():
            tag = 'tag_info'
            if '成功' in msg or '完成' in msg:
                tag = 'tag_ok'
            elif '失败' in msg or '错误' in msg or '异常' in msg:
                tag = 'tag_err'
            elif '跳过' in msg or '警告' in msg or '超时' in msg:
                tag = 'tag_warn'
            self.log_text.insert(tk.END, msg + '\n', tag)
            self.log_text.see(tk.END)
        try:
            self.root.after(0, _do)
        except:
            pass

    def _clear_log(self):
        self.log_text.delete('1.0', tk.END)

    def _on_drop(self, event):
        data = event.data
        if data:
            path = data.strip('{}')
            if os.path.isfile(path):
                self._load_resume(path)

    def _choose_resume(self):
        path = filedialog.askopenfilename(
            title="选择简历文件",
            filetypes=[
                ("简历文件", "*.pdf *.docx *.doc *.txt"),
                ("PDF文件", "*.pdf"),
                ("Word文档", "*.docx *.doc"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*"),
            ]
        )
        if path:
            self._load_resume(path)

    def _load_resume(self, path):
        try:
            self._append_log(f"📎 正在解析简历: {os.path.basename(path)}")
            data = self.resume_parser.load_file(path)
            self.resume_data = data
            self.resume_file_path = path
            self._update_resume_info(data)
            self.resume_status_lbl.config(text="已解析", style='Success.TLabel')
            self._append_log(
                f"✅ 简历解析完成: {data.get('name', '未知姓名')} | 技能 {len(data.get('skills', []))} 项"
            )
        except Exception as e:
            self._append_log(f"❌ 简历解析失败: {e}")
            messagebox.showerror("解析失败", f"简历解析失败:\n{e}")

    def _reparse_resume(self):
        if self.resume_file_path and os.path.exists(self.resume_file_path):
            self._load_resume(self.resume_file_path)
        else:
            messagebox.showwarning("提示", "请先选择简历文件")

    def _update_resume_info(self, data):
        self.name_lbl.config(text=data.get('name') or '-')
        self.phone_lbl.config(text=data.get('phone') or '-')
        self.email_lbl.config(text=data.get('email') or '-')
        self.target_lbl.config(text=data.get('target_position') or '-')

        skills = data.get('skills', [])
        self.skills_text.config(state=tk.NORMAL)
        self.skills_text.delete('1.0', tk.END)
        if skills:
            self.skills_text.insert(tk.END, '   ·   '.join(skills))
        else:
            self.skills_text.insert(tk.END, '（未识别到技能关键词，可手动在右上填写搜索词）')
        self.skills_text.config(state=tk.DISABLED)

        education = data.get('education', [])
        if education and isinstance(education[0], dict):
            lines = []
            for item in education:
                degree = item.get('degree', '').strip()
                school = item.get('school', '').strip()
                if degree or school:
                    lines.append('  ·  '.join(part for part in (degree, school) if part))
            education_text = '\n'.join(lines) if lines else '-'
        else:
            education_text = '   ·   '.join(education) if education else '-'
        self.edu_lbl.config(text=education_text)

    def _fill_from_resume(self):
        if self.resume_data:
            kw = self.resume_parser.get_search_keywords()
            if kw:
                self.keyword_entry.delete(0, tk.END)
                self.keyword_entry.insert(0, kw)
                self._append_log(f"🎯 已从简历提取关键词: {kw}")
            else:
                messagebox.showinfo("提示", "未能从简历中提取关键词，请手动输入")
        else:
            messagebox.showwarning("提示", "请先上传并解析简历")

    def _start_browser(self):
        def _run():
            ok = self.boss.init_driver()
            if ok:
                # Starting the browser should be a complete login action, not
                # leave an empty Chrome window waiting for a second click.
                if self.boss.open_login_page():
                    self._append_log("🌐 已打开 BOSS 直聘登录页，请使用 APP 扫码登录")
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "错误", "浏览器已启动，但未能打开 BOSS 直聘登录页，请查看日志"))
            else:
                self.root.after(0, lambda: messagebox.showerror("错误", "浏览器启动失败，请查看日志"))
        threading.Thread(target=_run, daemon=True).start()

    def _open_login(self):
        if not self.boss.driver:
            messagebox.showwarning("提示", "请先点击 [① 启动浏览器]")
            return

        def _run():
            self.boss.open_login_page()
        threading.Thread(target=_run, daemon=True).start()

    def _check_login(self):
        if not self.boss.driver:
            messagebox.showwarning("提示", "请先启动浏览器")
            return

        def _run():
            ok = self.boss.wait_for_login(timeout=10)
            if ok:
                self.login_status_lbl.config(text="已登录", style='Success.TLabel')
            else:
                self._append_log("⚠️ 未检测到登录状态，请先在浏览器中扫码登录")
        threading.Thread(target=_run, daemon=True).start()

    def _close_browser(self):
        if messagebox.askyesno("确认", "确定关闭浏览器？正在进行的投递会被中断。"):
            self.boss.close()
            self.login_status_lbl.config(text="未登录", style='Warning.TLabel')

    def _start_apply(self):
        if not self.boss.login_success:
            if self.boss.driver:
                self._append_log("🔐 检测登录状态中...")
                ok = self.boss.wait_for_login(timeout=8)
                if not ok:
                    messagebox.showwarning("未登录", "请先在浏览器中完成BOSS直聘扫码登录")
                    return
            else:
                messagebox.showwarning("未启动", "请先 [启动浏览器] 并扫码登录BOSS直聘")
                return

        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "请输入搜索关键词")
            return
        city = self.city_combo.get()

        try:
            max_pages = int(self.max_pages_spin.get())
            max_applies = int(self.max_apply_spin.get())
            dmin = int(self.delay_min.get())
            dmax = int(self.delay_max.get())
            if dmax < dmin:
                dmin, dmax = dmax, dmin
        except:
            messagebox.showerror("错误", "请输入有效的数字参数")
            return

        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL, text="⏸ 暂停")
        self.stop_btn.config(state=tk.NORMAL)

        self._append_log(f"🐱 猫猫提起了小粉桶，冲鸭！开始为「{keyword}」在 {city} 自动投递...")
        self.boss.start_auto_apply(
            keyword=keyword, city=city,
            max_pages=max_pages, max_applies=max_applies,
            delay_min=dmin, delay_max=dmax
        )

    def _pause_apply(self):
        st = self.boss.get_status()
        if st.get('paused'):
            self.boss.resume()
            self.pause_btn.config(text="⏸ 暂停")
        else:
            self.boss.pause()
            self.pause_btn.config(text="▶ 继续")

    def _stop_apply(self):
        if messagebox.askyesno("确认", "确定停止自动投递吗？"):
            self.boss.stop()

    def _reset_count(self):
        self.boss.reset_count()
        self.applied_num.config(text="0")
        self.failed_num.config(text="0")
        self.skipped_num.config(text="0")
        self._append_log("📊 统计数据已清零")

    def _update_status_loop(self):
        try:
            st = self.boss.get_status()
            self.applied_num.config(text=str(st['applied']))
            self.failed_num.config(text=str(st['failed']))
            self.skipped_num.config(text=str(st['skipped']))

            if st['login']:
                self.login_status_lbl.config(text="已登录", style='Success.TLabel')

            if st['running']:
                if st['paused']:
                    self.run_status.config(text="已暂停", fg=PALETTE["warning"])
                else:
                    self.run_status.config(text="跑路中...", fg=PALETTE["primary"])
                self.start_btn.config(state=tk.DISABLED)
                self.pause_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.NORMAL)
            else:
                self.run_status.config(text="空闲", fg=PALETTE["success"])
                self.start_btn.config(state=tk.NORMAL)
                self.pause_btn.config(state=tk.DISABLED, text="⏸ 暂停")
                self.stop_btn.config(state=tk.DISABLED)
        except:
            pass
        self.root.after(800, self._update_status_loop)

    def on_close(self):
        try:
            if self.boss.driver:
                if messagebox.askyesno("退出", "浏览器还在运行，是否关闭并退出？"):
                    self.boss.close()
                    self.root.destroy()
                else:
                    return
            else:
                self.root.destroy()
        except:
            self.root.destroy()


def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = JobApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
