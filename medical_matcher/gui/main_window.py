import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Canvas
from utils.data_handler import DataHandler
from gui.compare_window import CompareWindow
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class MainWindow(tk.Frame):
    def __init__(self, master=None, home_page=None):
        super().__init__(master)
        self.master = master
        self.home_page = home_page
        self.master.title("手术匹配系统")
        self.master.geometry('1200x700')
        
        # 从首页获取参数初始值
        if home_page:
            self.rural_value = float(home_page.rural_urban_value.get())
            self.worker_value = float(home_page.worker_value.get())
            self.weight_value = float(home_page.weight_value.get())
        else:
            self.rural_value = 1.0
            self.worker_value = 1.0
            self.weight_value = 1.0
        
        self.data_handler = DataHandler()
        self.groups = self.data_handler.groups
        
        # 预处理病种数据
        self.disease_info = self._preprocess_disease_info()
        
        self.create_widgets()
        self.update_disease_list()
        
    def _preprocess_disease_info(self):
        """预处理病种数据，避免重复计算"""
        disease_info = {}
        
        for group in self.groups:
            disease_name = group.disease_name
            if disease_name not in disease_info:
                # 查找保守治疗分值
                conservative_score = None
                min_score = float('inf')
                
                # 遍历同一病种的所有组
                for g in self.groups:
                    if g.disease_name == disease_name:
                        # 更新最低分值
                        if g.score < min_score:
                            min_score = g.score
                        # 检查是否是保守治疗
                        main_surgeries = ' / '.join(g.main_surgeries_names).lower()
                        if '保守治疗' in main_surgeries:
                            conservative_score = g.score
                            break
                
                # 如果没有找到保守治疗分值，使用最低分值
                standard_score = conservative_score if conservative_score is not None else min_score
                disease_info[disease_name] = standard_score
        
        return disease_info

    def create_widgets(self):
        # 创建顶部工具栏
        self.toolbar = tk.Frame(self.master)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 可以添加其他功能按钮
        self.preview_button = tk.Button(
            self.toolbar,
            text="组合预览",
            command=self.show_combinations,
            width=15
        )
        self.preview_button.pack(side=tk.LEFT, padx=5)
        
        # 在工具栏添加对比按钮
        self.compare_button = tk.Button(
            self.toolbar,
            text="分值对比",
            command=self.open_compare_window,
            width=15
        )
        self.compare_button.pack(side=tk.LEFT, padx=5)
        
        # 添加手术搜索按钮
        self.surgery_search_button = tk.Button(
            self.toolbar,
            text="手术搜索",
            command=self.open_surgery_search,
            width=15
        )
        self.surgery_search_button.pack(side=tk.LEFT, padx=5)
        
        # 在工具栏添加基层病种标识和分值显示框
        self.score_frame = tk.Frame(self.toolbar)
        self.score_frame.pack(side=tk.RIGHT, padx=10)
        
        # 添加基层病种标识
        self.basic_level_var = tk.StringVar(value="是否基层病种: -")
        tk.Label(self.score_frame, text="是否基层病种:", font=('Arial', 15, 'bold')).pack(side=tk.LEFT)
        tk.Label(self.score_frame, textvariable=self.basic_level_var, width=8).pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.score_frame, text="病种基准分值:", font=('Arial', 15, 'bold')).pack(side=tk.LEFT, padx=(10,0))
        self.base_score_var = tk.StringVar(value="-")
        tk.Label(self.score_frame, textvariable=self.base_score_var, width=8).pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.score_frame, text="当前选择分值:", font=('Arial', 15, 'bold')).pack(side=tk.LEFT, padx=(10,0))
        self.current_score_var = tk.StringVar(value="-")
        tk.Label(self.score_frame, textvariable=self.current_score_var, width=8).pack(side=tk.LEFT, padx=5)
        
        # 创建主容器
        self.main_container = tk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        self.main_container.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        # 左侧病种列表
        self.left_frame = tk.Frame(self.main_container)
        self.main_container.add(self.left_frame, width=300)
        
        # 创建上下分隔的框架
        left_top_frame = tk.Frame(self.left_frame)
        left_top_frame.pack(fill=tk.BOTH, expand=True)
        
        # 病种搜索框移到上部框架
        search_frame = tk.Frame(left_top_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 标签
        tk.Label(search_frame, text="搜索病种:").pack(side=tk.LEFT)
        
        # 搜索框
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_disease_list)
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 创建树形列表框架
        tree_frame = tk.Frame(left_top_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # 病种树形列表
        self.disease_tree = ttk.Treeview(
            tree_frame,
            columns=('standard_score', 'name'),
            show='headings',
            height=25  # 减小高度，为下方详情框留出空间
        )
        
        # 修改列标题，添加排序功能
        self.disease_tree.heading('standard_score', text='标准分值', 
                                command=lambda: self.sort_disease_list('standard_score', False))
        self.disease_tree.heading('name', text='病种名称')
        
        # 调整列宽
        self.disease_tree.column('standard_score', width=80, anchor='e')
        self.disease_tree.column('name', width=200)
        
        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(
            tree_frame,
            orient=tk.VERTICAL,
            command=self.disease_tree.yview
        )
        self.disease_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # 调整树形列表和滚动条的布局
        self.disease_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.disease_tree.bind('<<TreeviewSelect>>', self.on_select_disease)
        
        # 添加左下方的病种详情框
        left_bottom_frame = tk.Frame(self.left_frame, bg='#2b2b2b')
        left_bottom_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)
        
        # 创建标题标签
        title_frame = tk.Frame(left_bottom_frame, bg='#2b2b2b')
        title_frame.pack(fill=tk.X)
        
        tk.Label(
            title_frame, 
            text="病种详情", 
            font=('Arial', 12, 'bold'),
            fg='white',
            bg='#2b2b2b',
            padx=5,
            pady=2
        ).pack(side=tk.LEFT)
        
        # 创建详情文本框
        self.disease_detail = tk.Text(
            left_bottom_frame, 
            height=3,  # 减小高度
            wrap=tk.WORD,
            font=('Arial', 14, 'bold'),  # 加大字体
            bg='#2b2b2b',
            fg='white',
            relief=tk.FLAT,
            padx=5,
            pady=5
        )
        self.disease_detail.pack(fill=tk.BOTH, expand=True)
        self.disease_detail.config(state='disabled')
        
        # 在创建完所有控件后设置焦点
        self.search_entry.focus_set()
        
        # 右侧框架
        self.right_frame = tk.Frame(self.main_container)
        self.main_container.add(self.right_frame)
        
        # 右侧上部：手术列表
        self.detail_frame = tk.Frame(self.right_frame)
        self.detail_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加搜索框框架
        self.surgery_search_frame = tk.Frame(self.detail_frame)
        self.surgery_search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(self.surgery_search_frame, text="搜索手术:").pack(side=tk.LEFT)
        self.surgery_search_var = tk.StringVar()
        self.surgery_search_var.trace('w', self.filter_surgery_list)
        self.surgery_search_entry = tk.Entry(
            self.surgery_search_frame,
            textvariable=self.surgery_search_var,
            width=30
        )
        self.surgery_search_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 详细信息表
        self.detail_tree = ttk.Treeview(
            self.detail_frame,
            columns=('main_surgery', 'other_surgery', 'surgery_count', 'score', 'rural_balance'),
            show='headings',
            height=15
        )
        
        # 设置列
        self.detail_tree.heading('main_surgery', text='主要手术')
        self.detail_tree.heading('other_surgery', text='其他手术')
        self.detail_tree.heading('surgery_count', text='操作数')
        self.detail_tree.heading('score', text='分值', command=lambda: self.treeview_sort_column('score', False))
        self.detail_tree.heading('rural_balance', text='城乡盈亏平衡值', command=lambda: self.treeview_sort_column('rural_balance', False))
        
        # 调整列宽和对齐式
        self.detail_tree.column('main_surgery', width=300)
        self.detail_tree.column('other_surgery', width=200)
        self.detail_tree.column('surgery_count', width=60, anchor='center')
        self.detail_tree.column('score', width=80, anchor='e')
        self.detail_tree.column('rural_balance', width=150, anchor='e')
        
        # 添加滚动条
        detail_scrollbar = ttk.Scrollbar(
            self.detail_frame,
            orient=tk.VERTICAL,
            command=self.detail_tree.yview
        )
        self.detail_tree.configure(yscrollcommand=detail_scrollbar.set)
        
        self.detail_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.detail_tree.bind('<<TreeviewSelect>>', self.on_select_surgery)
        
        # 右侧下部：手术信息展示三个框）
        self.info_frame = tk.Frame(self.right_frame)
        self.info_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        # 创建三个等宽的框架
        self.surgery_frames = tk.PanedWindow(self.info_frame, orient=tk.HORIZONTAL)
        self.surgery_frames.pack(fill=tk.BOTH, expand=True)
        
        # 主要手术框架
        self.main_surgery_frame = tk.Frame(self.surgery_frames)
        self.surgery_frames.add(self.main_surgery_frame, width=300)  # 设置初始宽度
        
        tk.Label(self.main_surgery_frame, text="主要手术:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.main_surgery_info = tk.Text(self.main_surgery_frame, wrap=tk.WORD, height=10)
        self.main_surgery_info.pack(fill=tk.BOTH, expand=True)
        
        # 次要手术1框架
        self.other_surgery_frame1 = tk.Frame(self.surgery_frames)
        self.surgery_frames.add(self.other_surgery_frame1, width=300)  # 设置初始宽度
        
        tk.Label(self.other_surgery_frame1, text="次要手术1:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.other_surgery_info1 = tk.Text(self.other_surgery_frame1, wrap=tk.WORD, height=10)
        self.other_surgery_info1.pack(fill=tk.BOTH, expand=True)
        
        # 次要手术2框
        self.other_surgery_frame2 = tk.Frame(self.surgery_frames)
        self.surgery_frames.add(self.other_surgery_frame2, width=300)  # 设置初始宽度
        
        tk.Label(self.other_surgery_frame2, text="次要手术2:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.other_surgery_info2 = tk.Text(self.other_surgery_frame2, wrap=tk.WORD, height=10)
        self.other_surgery_info2.pack(fill=tk.BOTH, expand=True)
        
        # 添加计算域
        self.calculation_frame = tk.Frame(self.right_frame)
        self.calculation_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 保留链路图
        self.chart_frame = tk.Frame(self.calculation_frame)
        self.chart_frame.pack(fill=tk.X, pady=10)
        
        # 创建画布
        self.result_canvas = Canvas(self.chart_frame, height=150, bg='#2b2b2b')
        self.result_canvas.pack(fill=tk.X, padx=5)

    def show_combinations(self):
        """显示当前选中病种的所有组合预览"""
        # 获取当前选中的病种
        selection = self.disease_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个病种")
            return
        
        selected_disease = self.disease_tree.item(selection[0])['values'][1]
        
        # 创建预览窗口
        preview_window = tk.Toplevel(self.master)
        preview_window.title(f"{selected_disease} - 手术组合推荐")
        preview_window.geometry("1920x900")  # 增加高度
        preview_window.state('zoomed')  # 默认最大化窗口
        preview_window.configure(bg='#2b2b2b')
        
        # 创建顶部框架
        top_frame = tk.Frame(preview_window, bg='#2b2b2b')
        top_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 在顶部显示病种名称
        tk.Label(
            top_frame,
            text=f"病种：{selected_disease}",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#2b2b2b'
        ).pack(side=tk.LEFT)
        
        # 创建搜索框架
        search_frame = tk.Frame(preview_window, bg='#2b2b2b')
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 搜索标签和输入框
        tk.Label(
            search_frame,
            text="搜索手术:",
            font=('Arial', 10),
            fg='white',
            bg='#2b2b2b'
        ).pack(side=tk.LEFT)
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=search_var,
            width=40
        )
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # 在搜索框右侧添加分隔符
        tk.Label(
            search_frame,
            text="|",
            font=('Arial', 10),
            fg='#666666',
            bg='#2b2b2b'
        ).pack(side=tk.LEFT, padx=10)
        
        # 在搜索框后面直接添加筛选勾选框
        filter_vars = {
            1: tk.BooleanVar(value=True),
            2: tk.BooleanVar(value=True), 
            3: tk.BooleanVar(value=True)
        }
        
        for i in range(1,4):
            tk.Checkbutton(
                search_frame,
                text=f"{i}个操作",
                variable=filter_vars[i],
                command=lambda: update_combinations(),
                bg='#2b2b2b',
                fg='white',
                selectcolor='#444444',
                activebackground='#2b2b2b',
                activeforeground='white'
            ).pack(side=tk.LEFT, padx=5)
        
        # 修改主滚动区域的边距
        main_frame = tk.Frame(preview_window, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        canvas = tk.Canvas(main_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        class DarkButton(tk.Label):
            """自定义深色主题按钮"""
            def __init__(self, master, text, command):
                super().__init__(
                    master,
                    text=text,
                    font=('Arial', 10),
                    fg='#AAAAAA',
                    bg='#333333',
                    padx=10,
                    pady=3,
                    cursor='heart'  # 将 cursor 从 'hand2' 改为 'heart'
                )
                self.command = command
                self.bind('<Button-1>', lambda e: self.command())
                self.bind('<Enter>', self._on_enter)
                self.bind('<Leave>', self._on_leave)
                
            def _on_enter(self, e):
                self.configure(bg='#444444', fg='#FFFFFF')
                
            def _on_leave(self, e):
                self.configure(bg='#333333', fg='#AAAAAA')
        
        def create_card(parent, group_num, group, surgery_count):
            """创建卡片"""
            # 计算基准分值（保守治疗或最低分值）
            conservative_score = None
            min_score = float('inf')
            for g in self.groups:
                if g.disease_name == group.disease_name:
                    # 更新最低分值
                    if g.score < min_score:
                        min_score = g.score
                    # 检查是否是保守治疗
                    main_surgeries = ' / '.join(g.main_surgeries_names).lower()
                    if '保守治疗' in main_surgeries:
                        conservative_score = g.score
                        break
            
            # 使用保守治疗分值或最低分值作为基准
            base_score = conservative_score if conservative_score is not None else min_score
            
            # 计算盈亏平衡值
            is_basic = self.data_handler.is_basic_level_disease(group.disease_name)
            if is_basic:
                rural_balance = group.score * self.rural_value
                worker_balance = group.score * self.worker_value
            else:
                rural_balance = group.score * self.weight_value * self.rural_value
                worker_balance = group.score * self.weight_value * self.worker_value
            
            # 创建卡片主框架
            card = tk.Frame(parent, bg='#333333', highlightbackground='#444444', highlightthickness=1)
            
            # 添加顶部工具栏框架
            toolbar = tk.Frame(card, bg='#333333')
            toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
            
            # 添加勾选框
            card_selected = tk.BooleanVar()
            checkbox = tk.Checkbutton(
                toolbar,
                variable=card_selected,
                command=lambda: on_card_selected(card, group, card_selected),
                bg='#333333',
                activebackground='#333333',
                selectcolor='#444444'
            )
            checkbox.pack(side=tk.LEFT)
            
            # 将整个卡片绑定点击事件
            def on_card_click(event):
                card_selected.set(not card_selected.get())
                on_card_selected(card, group, card_selected)
            
            # 为卡片的所有子组件绑定点击事件
            def bind_click_to_children(widget):
                widget.bind('<Button-1>', on_card_click)
                for child in widget.winfo_children():
                    if not isinstance(child, tk.Checkbutton):  # 跳过勾选框本身
                        child.bind('<Button-1>', on_card_click)
                        if isinstance(child, tk.Frame):
                            bind_click_to_children(child)
            
            # 绑定点击事件到卡片及其所有子组件
            bind_click_to_children(card)
            
            # 添加右上角功能按钮
            button_frame = tk.Frame(toolbar, bg='#333333')
            button_frame.pack(side=tk.RIGHT)
            
            # 使用自定义按钮
            copy_btn = DarkButton(
                button_frame,
                text="复制",
                command=lambda: copy_card_content(group)
            )
            copy_btn.pack(side=tk.RIGHT, padx=2)
            
            apply_btn = DarkButton(
                button_frame,
                text="应用",
                command=lambda: self.apply_combination(group)
            )
            apply_btn.pack(side=tk.RIGHT, padx=2)
            
            # 根据操作数设置标题栏颜色
            header_colors = {
                1: '#FFFFFF',  # 白色
                2: '#4CAF50',  # 绿色
                3: '#2196F3'   # 蓝色
            }
            header_bg = '#333333'  # 默认背景色
            
            # 标题栏
            header = tk.Frame(card, bg=header_bg)
            header.pack(fill=tk.X, padx=10, pady=5)
            
            # 左侧标题（组合序号和操作数）
            title_frame = tk.Frame(header, bg=header_bg)
            title_frame.pack(side=tk.LEFT)
            
            # 获取对应的文字颜色
            text_color = header_colors.get(surgery_count, '#FFFFFF')
            
            # 将标题移到勾选框后面
            checkbox.pack(side=tk.LEFT)
            tk.Label(
                toolbar,  # 注意这里改为 toolbar 而不是 title_frame
                text=f"序号{group_num}-操作数:{surgery_count}",  # 将"组合"改为"序号"
                font=('Arial', 14, 'bold'),
                fg=text_color,
                bg='#333333',
                anchor='w'
            ).pack(side=tk.LEFT, padx=(5, 0))  # 添加左边距
            
            # 右侧分值框架
            score_frame = tk.Frame(header, bg=header_bg)
            score_frame.pack(side=tk.RIGHT)
            
            # 基础分值显示
            tk.Label(
                score_frame,
                text=f"分值：{group.score}",
                font=('Arial', 14, 'bold'),
                fg=text_color,
                bg=header_bg
            ).pack(side=tk.LEFT)
            
            # 如果有提升值，显示在同一行
            if group.score > base_score:
                increase = group.score - base_score
                tk.Label(
                    score_frame,
                    text=f" ↑{increase:.0f}",  # 使用向上箭头，去掉括号和加号
                    font=('Arial', 14, 'bold'),
                    fg='#FF4444',  # 红色
                    bg=header_bg
                ).pack(side=tk.LEFT)
            
            # 盈亏平衡值
            balance_frame = tk.Frame(card, bg='#333333')
            balance_frame.pack(fill=tk.X, padx=8, pady=(0,5))
            
            # 创建城乡盈亏平衡值行框架
            rural_frame = tk.Frame(balance_frame, bg='#333333')
            rural_frame.pack(fill=tk.X)
            
            tk.Label(
                rural_frame,
                text=f"城乡盈亏平衡值：¥{rural_balance:.2f}",
                font=('Arial', 13, 'bold'),
                fg='white',
                bg='#333333'
            ).pack(side=tk.LEFT)
            
            # 如果有提升值，显示在同一行
            if group.score > base_score:
                increase_balance = (group.score - base_score) * (self.rural_value if is_basic else self.weight_value * self.rural_value)
                tk.Label(
                    rural_frame,
                    text=f" ↑{increase_balance:.2f}",
                    font=('Arial', 13, 'bold'),
                    fg='#FF4444',
                    bg='#333333'
                ).pack(side=tk.LEFT)
            
            # 职工盈亏平衡值
            worker_frame = tk.Frame(balance_frame, bg='#333333')
            worker_frame.pack(fill=tk.X)
            
            tk.Label(
                worker_frame,
                text=f"职工盈亏平衡值：¥{worker_balance:.2f}",
                font=('Arial', 13, 'bold'),
                fg='white',
                bg='#333333'
            ).pack(side=tk.LEFT)
            
            # 如果有提升值，显示在同一行
            if group.score > base_score:
                increase_balance = (group.score - base_score) * (self.worker_value if is_basic else self.weight_value * self.worker_value)
                tk.Label(
                    worker_frame,
                    text=f" ↑{increase_balance:.2f}",
                    font=('Arial', 13, 'bold'),
                    fg='#FF4444',
                    bg='#333333'
                ).pack(side=tk.LEFT)
            
            # 主要手术标题
            tk.Label(
                card,
                text="主要手术:",
                font=('Arial', 13, 'bold'),  # 从14改为13
                fg='white',
                bg='#333333',
                anchor='w'
            ).pack(fill=tk.X, padx=8, pady=(8,4))
            
            # 主要手术列表
            for surgery in group.main_surgeries_names:
                tk.Label(
                    card,
                    text=f"- {surgery}",
                    font=('Arial', 13),  # 从14改为13
                    fg='white',
                    bg='#333333',
                    anchor='w',
                    wraplength=380,
                    justify=tk.LEFT
                ).pack(fill=tk.X, padx=16)
            
            # 其他手术（如果有）
            if group.other_surgeries_names:
                surgery_groups = group.other_surgeries_names.split('+')
                
                # 显示次要手术（第一组）
                if len(surgery_groups) > 0 and surgery_groups[0].strip():
                    tk.Label(
                        card,
                        text="次要手术:",
                        font=('Arial', 13, 'bold'),  # 从14改为13
                        fg='#4CAF50',
                        bg='#333333',
                        anchor='w'
                    ).pack(fill=tk.X, padx=8, pady=(8,4))
                    
                    surgeries = [s.strip() for s in surgery_groups[0].split('/')]
                    for surgery in surgeries:
                        if surgery.strip():
                            tk.Label(
                                card,
                                text=f"○ {surgery.strip()}",
                                font=('Arial', 13),  # 从14改为13
                                fg='#4CAF50',
                                bg='#333333',
                                anchor='w',
                                wraplength=380,
                                justify=tk.LEFT
                            ).pack(fill=tk.X, padx=16)
                
                # 显示搭配手术（第二组）
                if len(surgery_groups) > 1 and surgery_groups[1].strip():
                    tk.Label(
                        card,
                        text="搭配手术:",
                        font=('Arial', 13, 'bold'),  # 从14改为13
                        fg='#2196F3',
                        bg='#333333',
                        anchor='w'
                    ).pack(fill=tk.X, padx=8, pady=(8,4))
                    
                    surgeries = [s.strip() for s in surgery_groups[1].split('/')]
                    for surgery in surgeries:
                        if surgery.strip():
                            tk.Label(
                                card,
                                text=f"□ {surgery.strip()}",
                                font=('Arial', 13),  # 从14改为13
                                fg='#2196F3',
                                bg='#333333',
                                anchor='w',
                                wraplength=380,
                                justify=tk.LEFT
                            ).pack(fill=tk.X, padx=16)
            
            # 添加底部信息栏
            footer = tk.Frame(card, bg='#333333')
            footer.pack(fill=tk.X, padx=8, pady=5)
            
            # 添加手术编码信息（如果有）
            if hasattr(group, 'surgery_codes') and group.surgery_codes:
                tk.Label(
                    footer,
                    text=f"手术编码: {group.surgery_codes}",
                    font=('Arial', 10),
                    fg='#888888',
                    bg='#333333',
                    anchor='w'
                ).pack(side=tk.LEFT)
            
            # 添加备注信息（如果有）
            if hasattr(group, 'notes') and group.notes:
                tk.Label(
                    footer,
                    text=f"备注: {group.notes}",
                    font=('Arial', 10),
                    fg='#888888',
                    bg='#333333',
                    anchor='w'
                ).pack(side=tk.LEFT, padx=(10, 0))
            
            return card
        
        def copy_card_content(group):
            """复制卡片内容到剪贴板"""
            content = []
            content.append(f"病种：{group.disease_name}")
            content.append(f"分值：{group.score}")
            content.append("\n主要手术：")
            for surgery in group.main_surgeries_names:
                content.append(f"- {surgery}")
            
            if group.other_surgeries_names:
                surgery_groups = group.other_surgeries_names.split('+')
                if surgery_groups[0].strip():
                    content.append("\n次要手术：")
                    for surgery in surgery_groups[0].split('/'):
                        if surgery.strip():
                            content.append(f"○ {surgery.strip()}")
                
                if len(surgery_groups) > 1 and surgery_groups[1].strip():
                    content.append("\n搭配手术：")
                    for surgery in surgery_groups[1].split('/'):
                        if surgery.strip():
                            content.append(f"□ {surgery.strip()}")
            
            # 添加手术编码和备注信息（如果有）
            if hasattr(group, 'surgery_codes') and group.surgery_codes:
                content.append(f"\n手术编码：{group.surgery_codes}")
            if hasattr(group, 'notes') and group.notes:
                content.append(f"\n备注：{group.notes}")
            
            # 复制到剪贴板
            self.master.clipboard_clear()
            self.master.clipboard_append('\n'.join(content))
            
            # 显示提示消息
            messagebox.showinfo("提示", "内容已复制到剪贴板")
        
        def update_combinations(*args):
            # 清空现有内容
            for widget in content_frame.winfo_children():
                widget.destroy()
            
            # 获取搜索文本并分割成关键词列表
            search_terms = [term.strip().lower() for term in search_var.get().split() if term.strip()]
            
            # 获取并过滤组合
            related_groups = []
            for group in self.groups:
                if group.disease_name != selected_disease:
                    continue
                    
                # 计算操作数
                surgery_count = 1
                if group.other_surgeries_names:
                    surgery_groups = [g.strip() for g in group.other_surgeries_names.split('+')]
                    if surgery_groups[0]:
                        surgery_count += 1
                    if len(surgery_groups) > 1 and surgery_groups[1]:
                        surgery_count += 1
                
                # 检查操作数是否被选中
                if not filter_vars[surgery_count].get():
                    continue
                    
                # 检查搜索词匹配
                all_surgeries_text = (
                    ' '.join(surgery.lower() for surgery in group.main_surgeries_names) +
                    ' ' + (group.other_surgeries_names.lower() if group.other_surgeries_names else '')
                )
                
                if not search_terms or all(term in all_surgeries_text for term in search_terms):
                    related_groups.append(group)
            
            # 按分值排序
            related_groups.sort(key=lambda x: x.score, reverse=True)
            
            # 修改为每行4个卡片的布局
            current_row = None
            for i, group in enumerate(related_groups, 1):
                # 每四个组合创建新行
                if (i-1) % 4 == 0:
                    current_row = tk.Frame(content_frame, bg='#2b2b2b')
                    current_row.pack(fill=tk.X, pady=5)
                    current_row.grid_columnconfigure((0,1,2,3), weight=1)
                
                # 计算当前组合的操作数
                group_surgery_count = 1
                if group.other_surgeries_names:
                    surgery_groups = [g.strip() for g in group.other_surgeries_names.split('+')]
                    if surgery_groups[0]:
                        group_surgery_count += 1
                    if len(surgery_groups) > 1 and surgery_groups[1]:
                        group_surgery_count += 1
                
                # 使用正确的操作数创建卡片
                card = create_card(current_row, i, group, group_surgery_count)
                card.grid(row=0, 
                         column=(i-1)%4,
                         sticky='nsew', 
                         padx=10,
                         pady=5)
                
                # 如果有搜索词，高亮匹配的文本
                if search_terms:
                    for widget in card.winfo_children():
                        if isinstance(widget, tk.Label):
                            text = widget.cget('text')
                            for term in search_terms:
                                if term in text.lower():
                                    widget.configure(fg='#FFA500')  # 使用橙色高亮显示匹配文本
                                    break
        
        # 配置滚动
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建窗口
        canvas.create_window((0, 0), window=content_frame, anchor='nw')
        
        # 配置滚动区域
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        content_frame.bind('<Configure>', on_frame_configure)
        
        # 绑定搜索事件
        search_var.trace('w', update_combinations)
        
        # 初始显示
        update_combinations()
        
        # 修改鼠标滚轮绑定函数
        def _on_mousewheel(event):
            # 根据不同平台处理滚轮事件
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")
        
        # 绑定鼠标滚轮事件到画布和内容框架
        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
        canvas.bind_all("<Button-4>", _on_mousewheel)    # Linux up
        canvas.bind_all("<Button-5>", _on_mousewheel)    # Linux down
        
        # 在窗口关闭时清理滚轮绑定
        def on_closing():
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
            preview_window.destroy()
        
        preview_window.protocol("WM_DELETE_WINDOW", on_closing)

        # 添加对比按钮框架
        compare_frame = tk.Frame(preview_window, bg='#2b2b2b')
        compare_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 添加对比按钮
        compare_btn = tk.Button(
            compare_frame,
            text="对比选中组合",
            command=lambda: compare_selected_cards(),
            state='disabled'  # 初始禁用
        )
        compare_btn.pack(side=tk.RIGHT)
        
        # 用于存储选中的卡片
        selected_cards = []
        
        def on_card_selected(card, group, selected):
            """处理卡片选中状态变化"""
            if selected.get():
                if len(selected_cards) < 3:
                    selected_cards.append((card, group))
                    card.configure(highlightbackground='#2196F3')
                else:
                    selected.set(False)
                    messagebox.showinfo("提示", "最多只能选择3个组合进行对比")
            else:
                selected_cards.remove((card, group))
                card.configure(highlightbackground='#444444')
            
            # 更新对比按钮状态
            compare_btn.configure(state='normal' if len(selected_cards) >= 2 else 'disabled')
        
        def compare_selected_cards():
            """对比选中的组合"""
            if len(selected_cards) < 2:
                messagebox.showinfo("提示", "请至少选择2个组合进行对比")
                return
            
            # 创建对比窗口
            compare_window = tk.Toplevel(preview_window)
            compare_window.title("组合对比")
            window_width = 1200 if len(selected_cards) == 2 else 1800
            compare_window.geometry(f"{window_width}x800")
            compare_window.configure(bg='#2b2b2b')
            
            # 获取组合并按分值排序
            groups = [card[1] for card in selected_cards]
            groups.sort(key=lambda x: x.score)
            
            # 显示病种名称（居中）
            tk.Label(compare_window, text=groups[0].disease_name, font=('Arial', 20, 'bold'),
                    fg='white', bg='#2b2b2b').pack(pady=10)
            
            # 创建主容器
            container = tk.Frame(compare_window, bg='#2b2b2b')
            container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            if len(groups) == 2:
                # 两个组合的对比
                container.columnconfigure(0, weight=1)
                container.columnconfigure(1, weight=1)
                
                # 左侧组合（低分值）
                left_frame = tk.Frame(container, bg='#2b2b2b')
                left_frame.grid(row=0, column=0, sticky='nsew', padx=5)
                create_group_frame(left_frame, groups[0], "低分组合")
                
                # 右侧组合（高分值）
                right_frame = tk.Frame(container, bg='#2b2b2b')
                right_frame.grid(row=0, column=1, sticky='nsew', padx=5)
                create_group_frame(right_frame, groups[1], "高分组合", [groups[0]])
            else:
                # 三个组合的对比
                container.columnconfigure(0, weight=1)
                container.columnconfigure(1, weight=1)
                container.columnconfigure(2, weight=1)
                
                # 左侧组合（低分值）
                left_frame = tk.Frame(container, bg='#2b2b2b')
                left_frame.grid(row=0, column=0, sticky='nsew', padx=5)
                create_group_frame(left_frame, groups[0], "低分组合")
                
                # 中间组合（中分值）
                middle_frame = tk.Frame(container, bg='#2b2b2b')
                middle_frame.grid(row=0, column=1, sticky='nsew', padx=5)
                create_group_frame(middle_frame, groups[1], "中分组合", [groups[0]])
                
                # 右侧组合（高分值）
                right_frame = tk.Frame(container, bg='#2b2b2b')
                right_frame.grid(row=0, column=2, sticky='nsew', padx=5)
                create_group_frame(right_frame, groups[2], "高分组合", [groups[0], groups[1]])
        
        def create_group_frame(parent, group, title, compare_groups=None):
            """创建组合信息框架"""
            # 添加标题
            tk.Label(parent, text=title, font=('Arial', 16, 'bold'),
                    fg='white', bg='#2b2b2b').pack(pady=5)
            
            # 分值信息框
            score_frame = tk.LabelFrame(parent, text="分值信息", font=('Arial', 14, 'bold'),
                                      fg='white', bg='#2b2b2b', padx=10, pady=5)
            score_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # 基础分值（带差异显示）
            score_frame_row = tk.Frame(score_frame, bg='#2b2b2b')
            score_frame_row.pack(fill=tk.X)
            
            tk.Label(score_frame_row, text=f"基础分值：{int(group.score)}", 
                    font=('Arial', 14, 'bold'), fg='white', bg='#2b2b2b').pack(side=tk.LEFT)
            
            if compare_groups and title == "高分组合":
                # 对于高分组合，先显示与中分组合的差额（绿色），再显示与低分组合的差额（红色）
                if len(compare_groups) >= 2:  # 有中分组合和低分组合
                    # 与中分组合的差额（绿色）
                    diff_middle = int(group.score - compare_groups[1].score)
                    tk.Label(score_frame_row, text=f" ↑{diff_middle}", 
                            font=('Arial', 14, 'bold'), fg='#4CAF50', bg='#2b2b2b').pack(side=tk.LEFT)
                    # 与低分组合的差额（红色）
                    diff_low = int(group.score - compare_groups[0].score)
                    tk.Label(score_frame_row, text=f" ↑{diff_low}", 
                            font=('Arial', 14, 'bold'), fg='#F44336', bg='#2b2b2b').pack(side=tk.LEFT)
                elif len(compare_groups) == 1:  # 只有低分组合
                    diff = int(group.score - compare_groups[0].score)
                    tk.Label(score_frame_row, text=f" ↑{diff}", 
                            font=('Arial', 14, 'bold'), fg='#F44336', bg='#2b2b2b').pack(side=tk.LEFT)
            elif compare_groups:
                # 其他组合保持原有逻辑
                if len(compare_groups) >= 1:
                    diff1 = int(group.score - compare_groups[0].score)
                    tk.Label(score_frame_row, text=f" ↑{diff1}", 
                            font=('Arial', 14, 'bold'), fg='#4CAF50', bg='#2b2b2b').pack(side=tk.LEFT)
                if len(compare_groups) >= 2:
                    diff2 = int(group.score - compare_groups[1].score)
                    tk.Label(score_frame_row, text=f" ↑{diff2}", 
                            font=('Arial', 14, 'bold'), fg='#F44336', bg='#2b2b2b').pack(side=tk.LEFT)
            
            # 城乡盈亏平衡值（带差异显示）
            is_basic = self.data_handler.is_basic_level_disease(group.disease_name)
            rural_balance = group.score * self.rural_value if is_basic else group.score * self.weight_value * self.rural_value
            
            rural_frame_row = tk.Frame(score_frame, bg='#2b2b2b')
            rural_frame_row.pack(fill=tk.X)
            
            tk.Label(rural_frame_row, text=f"城乡盈亏平衡值：¥{rural_balance:.2f}", 
                    font=('Arial', 14, 'bold'), fg='white', bg='#2b2b2b').pack(side=tk.LEFT)
            
            if compare_groups and title == "高分组合":
                # 对于高分组合，先显示与中分组合的差额（绿色），再显示与低分组合的差额（红色）
                if len(compare_groups) >= 2:  # 有中分组合和低分组合
                    # 与中分组合的差额（绿色）
                    other_rural_middle = compare_groups[1].score * self.rural_value if is_basic else compare_groups[1].score * self.weight_value * self.rural_value
                    diff_middle = int(rural_balance - other_rural_middle)
                    tk.Label(rural_frame_row, text=f" ↑{diff_middle}", 
                            font=('Arial', 14, 'bold'), fg='#4CAF50', bg='#2b2b2b').pack(side=tk.LEFT)
                    # 与低分组合的差额（红色）
                    other_rural_low = compare_groups[0].score * self.rural_value if is_basic else compare_groups[0].score * self.weight_value * self.rural_value
                    diff_low = int(rural_balance - other_rural_low)
                    tk.Label(rural_frame_row, text=f" ↑{diff_low}", 
                            font=('Arial', 14, 'bold'), fg='#F44336', bg='#2b2b2b').pack(side=tk.LEFT)
                elif len(compare_groups) == 1:  # 只有低分组合
                    other_rural = compare_groups[0].score * self.rural_value if is_basic else compare_groups[0].score * self.weight_value * self.rural_value
                    diff = int(rural_balance - other_rural)
                    tk.Label(rural_frame_row, text=f" ↑{diff}", 
                            font=('Arial', 14, 'bold'), fg='#F44336', bg='#2b2b2b').pack(side=tk.LEFT)
            elif compare_groups:
                # 其他组合保持原有逻辑
                if len(compare_groups) >= 1:
                    other_rural = compare_groups[0].score * self.rural_value if is_basic else compare_groups[0].score * self.weight_value * self.rural_value
                    diff1 = int(rural_balance - other_rural)
                    tk.Label(rural_frame_row, text=f" ↑{diff1}", 
                            font=('Arial', 14, 'bold'), fg='#4CAF50', bg='#2b2b2b').pack(side=tk.LEFT)
                if len(compare_groups) >= 2:
                    other_rural = compare_groups[1].score * self.rural_value if is_basic else compare_groups[1].score * self.weight_value * self.rural_value
                    diff2 = int(rural_balance - other_rural)
                    tk.Label(rural_frame_row, text=f" ↑{diff2}", 
                            font=('Arial', 14, 'bold'), fg='#F44336', bg='#2b2b2b').pack(side=tk.LEFT)
            
            # 职工盈亏平衡值（带差异显示）
            worker_balance = group.score * self.worker_value if is_basic else group.score * self.weight_value * self.worker_value
            
            worker_frame_row = tk.Frame(score_frame, bg='#2b2b2b')
            worker_frame_row.pack(fill=tk.X)
            
            tk.Label(worker_frame_row, text=f"职工盈亏平衡值：¥{worker_balance:.2f}", 
                    font=('Arial', 14, 'bold'), fg='white', bg='#2b2b2b').pack(side=tk.LEFT)
            
            if compare_groups and title == "高分组合":
                # 对于高分组合，先显示与中分组合的差额（绿色），再显示与低分组合的差额（红色）
                if len(compare_groups) >= 2:  # 有中分组合和低分组合
                    # 与中分组合的差额（绿色）
                    other_worker_middle = compare_groups[1].score * self.worker_value if is_basic else compare_groups[1].score * self.weight_value * self.worker_value
                    diff_middle = int(worker_balance - other_worker_middle)
                    tk.Label(worker_frame_row, text=f" ↑{diff_middle}", 
                            font=('Arial', 14, 'bold'), fg='#4CAF50', bg='#2b2b2b').pack(side=tk.LEFT)
                    # 与低分组合的差额（红色）
                    other_worker_low = compare_groups[0].score * self.worker_value if is_basic else compare_groups[0].score * self.weight_value * self.worker_value
                    diff_low = int(worker_balance - other_worker_low)
                    tk.Label(worker_frame_row, text=f" ↑{diff_low}", 
                            font=('Arial', 14, 'bold'), fg='#F44336', bg='#2b2b2b').pack(side=tk.LEFT)
                elif len(compare_groups) == 1:  # 只有低分组合
                    other_worker = compare_groups[0].score * self.worker_value if is_basic else compare_groups[0].score * self.weight_value * self.worker_value
                    diff = int(worker_balance - other_worker)
                    tk.Label(worker_frame_row, text=f" ↑{diff}", 
                            font=('Arial', 14, 'bold'), fg='#F44336', bg='#2b2b2b').pack(side=tk.LEFT)
            elif compare_groups:
                # 其他组合保持原有逻辑
                if len(compare_groups) >= 1:
                    other_worker = compare_groups[0].score * self.worker_value if is_basic else compare_groups[0].score * self.weight_value * self.worker_value
                    diff1 = int(worker_balance - other_worker)
                    tk.Label(worker_frame_row, text=f" ↑{diff1}", 
                            font=('Arial', 14, 'bold'), fg='#4CAF50', bg='#2b2b2b').pack(side=tk.LEFT)
                if len(compare_groups) >= 2:
                    other_worker = compare_groups[1].score * self.worker_value if is_basic else compare_groups[1].score * self.weight_value * self.worker_value
                    diff2 = int(worker_balance - other_worker)
                    tk.Label(worker_frame_row, text=f" ↑{diff2}", 
                            font=('Arial', 14, 'bold'), fg='#F44336', bg='#2b2b2b').pack(side=tk.LEFT)
            
            # 主要手术框
            main_surgery_frame = tk.LabelFrame(parent, text="主要手术", font=('Arial', 14, 'bold'),
                                             fg='white', bg='#2b2b2b', padx=10, pady=5)
            main_surgery_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # 显示主要手术（带差异标记）
            if compare_groups:
                other_surgeries = set(surgery for group in compare_groups for surgery in group.main_surgeries_names)
                for surgery in group.main_surgeries_names:
                    color = '#4CAF50' if surgery not in other_surgeries else 'white'
                    prefix = '+ ' if surgery not in other_surgeries else '• '
                    tk.Label(main_surgery_frame, text=f"{prefix}{surgery}", font=('Arial', 12),
                            fg=color, bg='#2b2b2b', wraplength=450, justify=tk.LEFT).pack(anchor='w')
            else:
                for surgery in group.main_surgeries_names:
                    tk.Label(main_surgery_frame, text=f"• {surgery}", font=('Arial', 12),
                            fg='white', bg='#2b2b2b', wraplength=450, justify=tk.LEFT).pack(anchor='w')
            
            # 其他手术框
            if group.other_surgeries_names:
                other_surgery_frame = tk.LabelFrame(parent, text="其他手术", font=('Arial', 14, 'bold'),
                                                  fg='white', bg='#2b2b2b', padx=10, pady=5)
                other_surgery_frame.pack(fill=tk.X, padx=10, pady=5)
                
                # 处理其他手术（带差异标记）
                surgery_groups = group.other_surgeries_names.split('+')
                if compare_groups:
                    other_surg_set = set(surgery for comp_group in compare_groups 
                                        for surgery in comp_group.other_surgeries_names.split('/') 
                                        if surgery.strip())
                else:
                    other_surg_set = set(surgery.strip() for surgery in group.other_surgeries_names.split('/') 
                                        if surgery.strip())
                
                # 显示次要手术（第一组）
                if surgery_groups[0].strip():
                    surgeries = [s.strip() for s in surgery_groups[0].split('/')]
                    for surgery in surgeries:
                        if surgery:
                            if compare_groups:
                                color = '#4CAF50' if surgery not in other_surg_set else '#4CAF50'
                                prefix = '+ ' if surgery not in other_surg_set else '○ '
                            else:
                                color = '#4CAF50'
                                prefix = '○ '
                            tk.Label(other_surgery_frame, text=f"{prefix}{surgery}", font=('Arial', 12),
                                    fg=color, bg='#2b2b2b', wraplength=450, justify=tk.LEFT).pack(anchor='w')
                
                # 显示搭配手术（第二组）
                if len(surgery_groups) > 1 and surgery_groups[1].strip():
                    surgeries = [s.strip() for s in surgery_groups[1].split('/')]
                    for surgery in surgeries:
                        if surgery:
                            if compare_groups:
                                color = '#4CAF50' if surgery not in other_surg_set else '#2196F3'
                                prefix = '+ ' if surgery not in other_surg_set else '□ '
                            else:
                                color = '#2196F3'
                                prefix = '□ '
                            tk.Label(other_surgery_frame, text=f"{prefix}{surgery}", font=('Arial', 12),
                                    fg=color, bg='#2b2b2b', wraplength=450, justify=tk.LEFT).pack(anchor='w')

    def apply_combination(self, group):
        """应用选中的组合"""
        # 在主界面选中对应的组合
        for item in self.detail_tree.get_children():
            values = self.detail_tree.item(item)['values']
            main_surgeries = values[0]
            other_surgeries = values[1]
            
            # 检查是否匹配当前组合
            if (main_surgeries == ' / '.join(group.main_surgeries_names) and
                other_surgeries == group.other_surgeries_names):
                # 选中该组合
                self.detail_tree.selection_set(item)
                self.detail_tree.see(item)
                self.on_select_surgery(None)  # 触发选择事件
                break

    def update_disease_list(self):
        # 清空树形列表
        for item in self.disease_tree.get_children():
            self.disease_tree.delete(item)
        
        # 获取所有不重复的病种名称及其标准分值
        disease_info = {}  # 用于存储病种名称和对应的分值
        
        for group in self.groups:
            disease_name = group.disease_name
            if disease_name not in disease_info:
                # 查找保守治疗分值
                conservative_score = None
                min_score = float('inf')
                
                # 遍历同一病种的所有组
                for g in self.groups:
                    if g.disease_name == disease_name:
                        # 更新最低分值
                        if g.score < min_score:
                            min_score = g.score
                        # 检查是否是保守治疗
                        main_surgeries = ' / '.join(g.main_surgeries_names).lower()
                        if '保守治疗' in main_surgeries:
                            conservative_score = g.score
                            break
                
                # 如果没有找到保守治疗分值，使用最低分值
                standard_score = conservative_score if conservative_score is not None else min_score
                disease_info[disease_name] = standard_score
        
        # 按病种名称排序并添加到树形列表
        for disease_name in sorted(disease_info.keys()):
            self.disease_tree.insert(
                '',
                'end',
                values=(
                    disease_info[disease_name],  # 标准分值
                    disease_name  # 病种名称
                )
            )

    def filter_disease_list(self, *args):
        """优化后的疾病列表过滤方法"""
        search_text = self.search_var.get().lower()
        
        # 清空树形列表
        for item in self.disease_tree.get_children():
            self.disease_tree.delete(item)
        
        # 获取当前排序状态
        current_sort = None
        current_reverse = False
        for col in ('standard_score', 'name'):
            header_text = self.disease_tree.heading(col)['text']
            if '▼' in header_text:
                current_sort = col
                current_reverse = True
                break
            elif '▲' in header_text:
                current_sort = col
                current_reverse = False
                break
        
        # 使用预处理的数据进行过滤
        filtered_items = [
            (score, name) 
            for name, score in self.disease_info.items() 
            if search_text in name.lower()
        ]
        
        # 如果有排序，应用排序
        if current_sort:
            col_index = 0 if current_sort == 'standard_score' else 1
            try:
                filtered_items.sort(
                    key=lambda x: float(x[col_index]) if col_index == 0 else x[col_index],
                    reverse=current_reverse
                )
            except ValueError:
                filtered_items.sort(key=lambda x: x[col_index], reverse=current_reverse)
        
        # 插入排序后的项目
        for item in filtered_items:
            self.disease_tree.insert('', 'end', values=item)

    def on_select_disease(self, event):
        selection = self.disease_tree.selection()
        if not selection:
            return
            
        # 清空手术搜索框
        self.surgery_search_var.set("")
        
        # 清空详细信息表格
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
            
        selected_item = self.disease_tree.item(selection[0])
        selected_disease = selected_item['values'][1]  # 改为 values[1]，因为病种名称现在在第二列
        
        # 判断是否为基层病种并更新显示
        is_basic_level = self.data_handler.is_basic_level_disease(selected_disease)
        self.basic_level_var.set("是" if is_basic_level else "否")
        
        # 获取选中病种的所有相关信息
        related_groups = [
            group for group in self.groups 
            if group.disease_name == selected_disease
        ]
        
        # 更新基准分值（最低分值）
        if related_groups:
            min_score = min(group.score for group in related_groups)
            self.base_score_var.set(str(min_score))
        else:
            self.base_score_var.set("-")
        
        # 清空当前选择分值
        self.current_score_var.set("-")
        
        # 更新详细信息表格
        for group in related_groups:
            main_surgeries_names = ' / '.join(group.main_surgeries_names)
            other_surgeries_names = group.other_surgeries_names
            score = group.score
            
            # 计算手术操作个数
            surgery_count = 1  # 主要手术至少有1个
            
            # 检查其他手术区域
            if other_surgeries_names:
                surgery_groups = [group.strip() for group in other_surgeries_names.split('+')]
                if surgery_groups[0].strip():  # 检查第一个其他手术区域
                    surgery_count += 1
                if len(surgery_groups) > 1 and surgery_groups[1].strip():  # 检查第二个其他手术区域
                    surgery_count += 1
            
            # 获取是否为基层病种
            is_basic_level = self.data_handler.is_basic_level_disease(selected_disease)
            
            # 使用保存的参数值计算城乡盈亏平衡值
            if is_basic_level:
                rural_balance = score * self.rural_value
            else:
                rural_balance = score * self.weight_value * self.rural_value
            
            self.detail_tree.insert(
                '',
                'end',
                values=(
                    main_surgeries_names,  # 不再包含操作数
                    other_surgeries_names,
                    surgery_count,  # 单独的操作数列
                    score,
                    f"{rural_balance:.2f}"
                )
            )
        
        # 更新病种详情显示
        self.disease_detail.config(state='normal')  # 临时允许编辑
        self.disease_detail.delete('1.0', tk.END)
        
        # 获取病种详细信息
        selected_item = self.disease_tree.item(selection[0])
        disease_name = selected_item['values'][1]
        
        # 只显示病种名称
        self.disease_detail.insert('1.0', disease_name)
        self.disease_detail.config(state='disabled')  # 恢复只读状态

    def on_select_surgery(self, event):
        selection = self.detail_tree.selection()
        if not selection:
            return
            
        # 获取选中行的信息
        item = self.detail_tree.item(selection[0])
        values = item['values']
        
        # 更新当前选择分值 - 修改这里，使用分值而不是操作数
        self.current_score_var.set(str(values[3]))  # values[3] 是分值列
        
        # 设置所有文本框为可编辑状态
        self.main_surgery_info.config(state='normal')
        self.other_surgery_info1.config(state='normal')
        self.other_surgery_info2.config(state='normal')
        
        # 清空所有文本框
        self.main_surgery_info.delete('1.0', tk.END)
        self.other_surgery_info1.delete('1.0', tk.END)
        self.other_surgery_info2.delete('1.0', tk.END)
        
        # 显示主要手术详细信息
        main_surgeries = values[0].split(' / ')
        for i, surgery in enumerate(main_surgeries, 1):
            self.main_surgery_info.insert(tk.END, f"{i}. {surgery}\n")
        
        # 显示其他手术详细信息
        if values[1]:
            # 按+割成组，确保处理所有空格况
            surgery_groups = [group.strip() for group in values[1].split('+')]
            
            # 显示第一组他手术
            if len(surgery_groups) > 0 and surgery_groups[0]:
                surgeries = [s.strip() for s in surgery_groups[0].split('/')]
                for j, surgery in enumerate(surgeries, 1):
                    if surgery:  # 确保不是空字符串
                        self.other_surgery_info1.insert(tk.END, f"1.{j} {surgery}\n")
            
            # 显示第二组其他手术
            if len(surgery_groups) > 1 and surgery_groups[1]:
                surgeries = [s.strip() for s in surgery_groups[1].split('/')]
                for j, surgery in enumerate(surgeries, 1):
                    if surgery:  # 确保不是空字符串
                        self.other_surgery_info2.insert(tk.END, f"2.{j} {surgery}\n")
        
        # 设置所有文本框为只读
        self.main_surgery_info.config(state='disabled')
        self.other_surgery_info1.config(state='disabled')
        self.other_surgery_info2.config(state='disabled')
        
        # 更新完其他信息后，触发计算
        self.calculate_results()

    def draw_result_chart(self, rural_min, rural_balance, rural_max, 
                         worker_min, worker_balance, worker_max, is_basic_level):
        """绘制结果链路图"""
        # 清空画布
        self.result_canvas.delete('all')
        
        # 获取画布尺寸
        canvas_width = self.result_canvas.winfo_width()
        canvas_height = self.result_canvas.winfo_height()
        
        # 设置边距和间距
        margin_x = 80
        margin_y = 30
        
        # 计算绘图区域
        chart_width = canvas_width - 2 * margin_x
        
        # 调整Y位置，增加间距
        rural_y = canvas_height * 1 // 3  # 城乡结果位置
        worker_y = canvas_height * 2 // 3  # 职工结果位置
        
        # 绘制标题 - 简化标题文本并靠左显示
        title_offset = 25  # 标题与链路的距离
        self.result_canvas.create_text(10, rural_y - title_offset,
                                     text="城乡", 
                                     fill='white', 
                                     anchor='w',
                                     font=('Arial', 10, 'bold'))
        self.result_canvas.create_text(10, worker_y - title_offset,
                                     text="职工", 
                                     fill='white', 
                                     anchor='w',
                                     font=('Arial', 10, 'bold'))
        
        # 绘制链路
        self._draw_value_chain(margin_x, chart_width, rural_y, 
                             rural_min, rural_balance, rural_max)
        self._draw_value_chain(margin_x, chart_width, worker_y, 
                             worker_min, worker_balance, worker_max)

    def _draw_value_chain(self, x_start, width, y, min_val, balance, max_val):
        """绘制单值链路"""
        # 计算三个点的x坐标
        x1 = x_start  # 最小值
        x2 = x_start + width // 2  # 平衡值
        x3 = x_start + width  # 最大值
        
        # 绘制连接线
        self.result_canvas.create_line(x1, y, x3, y, fill='#666666', width=2)
        
        # 绘制三个点
        point_radius = 5
        self.result_canvas.create_oval(x1-point_radius, y-point_radius, 
                                     x1+point_radius, y+point_radius, 
                                     fill='#4CAF50')
        self.result_canvas.create_oval(x2-point_radius, y-point_radius, 
                                     x2+point_radius, y+point_radius, 
                                     fill='#2196F3')
        self.result_canvas.create_oval(x3-point_radius, y-point_radius, 
                                     x3+point_radius, y+point_radius, 
                                     fill='#F44336')
        
        # 添加值标签，调整位置和字体
        label_y_offset = 20  # 标签与线的离
        
        # 每个值创建背景矩形
        for x, val in [(x1, min_val), (x2, balance), (x3, max_val)]:
            text = f"{val:.2f}"
            # 在文本下方绘制值
            self.result_canvas.create_text(x, y + label_y_offset,
                                         text=text,
                                         fill='white',
                                         font=('Arial', 10),
                                         anchor='n')  # 上对齐

    def calculate_results(self, *args):
        """计算并更新结果"""
        selection = self.detail_tree.selection()
        if not selection:
            return
        
        try:
            # 使用保存的参数值
            weight = self.weight_value
            rural_value = self.rural_value
            worker_value = self.worker_value
            
            # 获取选中行的分值 - 修改这里，使用正确的分值列索引
            item = self.detail_tree.item(selection[0])
            score = float(item['values'][3])  # 改为 values[3]，因为现在分值在第4列
            
            # 获取选中的病种名称
            disease_selection = self.disease_tree.selection()
            if disease_selection:
                disease_name = self.disease_tree.item(disease_selection[0])['values'][0]
                is_basic_level = self.data_handler.is_basic_level_disease(disease_name)
                
                # 计算盈亏平衡值
                if is_basic_level:
                    rural_balance = score * rural_value
                    worker_balance = score * worker_value
                else:
                    rural_balance = score * weight * rural_value
                    worker_balance = score * weight * worker_value
                
                # 计算范围
                rural_min = rural_balance * 0.6
                rural_max = rural_balance * 2.0
                worker_min = worker_balance * 0.6
                worker_max = worker_balance * 2.0
                
                # 绘制链路路图
                self.draw_result_chart(
                    rural_min, rural_balance, rural_max,
                    worker_min, worker_balance, worker_max,
                    is_basic_level
                )
                
        except ValueError:
            # 清空链路图
            self.result_canvas.delete('all')

    def open_compare_window(self):
        """打开对比窗口"""
        compare_window = CompareWindow(self.master, self.data_handler)

    def create_surgery_list(self):
        # ... 现有代码 ...
        
        # 修改列表显示格式
        self.surgery_list = ttk.Treeview(
            self, 
            columns=("手术名称", "权重系数", "城乡分值"),
            show="headings"
        )
        
        # 设置列标题
        self.surgery_list.heading("手术名称", text="手术名称")
        self.surgery_list.heading("权重系数", text="权重系数")
        self.surgery_list.heading("城乡分值", text="城乡分值")
        
        # 设置列宽
        self.surgery_list.column("手术名称", width=400)
        self.surgery_list.column("权重系数", width=100)
        self.surgery_list.column("城乡分值", width=100)
        
        # 插入数据时的修改
        for surgery in self.surgeries:
            self.surgery_list.insert(
                "", 
                "end", 
                values=(
                    surgery.name,
                    f"{surgery.weight:.3f}",  # 显示权重系数
                    f"{surgery.rural_urban_value}"  # 显示城乡分值
                )
            )
        
        # ... 其他列表相关代码 ...

    def calculate_balance_value(self, base_value, is_base_disease):
        # 如果是基层病种，直接乘以8
        if is_base_disease:
            return base_value * 8
        
        # 如果不是基层病种，则使用有的计算逻辑（包含权重系数）
        weight = self.get_weight_coefficient()  # 获取权重系数
        return base_value * weight * 8

    def update_params_from_home(self, rural_urban, worker, weight):
        """从首页更新参数"""
        self.rural_value = rural_urban
        self.worker_value = worker
        self.weight_value = weight
        # 更新当前显示的结果
        self.calculate_results()

    def filter_surgery_list(self, *args):
        search_text = self.surgery_search_var.get().lower()
        
        # 获取当前选中的病种
        disease_selection = self.disease_tree.selection()
        if not disease_selection:
            return
            
        selected_disease = self.disease_tree.item(disease_selection[0])['values'][1]
        
        # 获取当前排序状态
        current_sort = None
        current_reverse = False
        for col in ('main_surgery', 'other_surgery', 'score', 'rural_balance'):
            header_text = self.detail_tree.heading(col)['text']
            if '▼' in header_text:
                current_sort = col
                current_reverse = True
                break
            elif '▲' in header_text:
                current_sort = col
                current_reverse = False
                break
        
        # 清空详细信息表格
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
            
        # 获取选中病种的所有相关信息
        related_groups = [
            group for group in self.groups 
            if group.disease_name == selected_disease
        ]
        
        # 更新详细信息表格，加入搜索过滤
        filtered_items = []
        for group in related_groups:
            main_surgeries_names = ' / '.join(group.main_surgeries_names)
            other_surgeries_names = group.other_surgeries_names
            score = group.score
            
            # 计算手术操作个数
            surgery_count = 1  # 主要手术至少有1个
            
            # 检查其他手术区域
            if other_surgeries_names:
                surgery_groups = [group.strip() for group in other_surgeries_names.split('+')]
                if surgery_groups[0].strip():  # 检查第一个其他手术区域
                    surgery_count += 1
                if len(surgery_groups) > 1 and surgery_groups[1].strip():  # 检查第二个其他手术区域
                    surgery_count += 1
            
            # 如果搜索文本为空或者搜索文本在主要手术或次要手术中
            if (not search_text or 
                search_text in main_surgeries_names.lower() or 
                search_text in other_surgeries_names.lower()):
                
                # 获取是否为基层病种
                is_basic_level = self.data_handler.is_basic_level_disease(selected_disease)
                
                # 使用保存的参数值计算城乡盈亏平衡值
                if is_basic_level:
                    rural_balance = score * self.rural_value
                else:
                    rural_balance = score * self.weight_value * self.rural_value
                
                filtered_items.append((
                    main_surgeries_names,  # 不再包含操作数
                    other_surgeries_names,
                    surgery_count,  # 添加手术操作数
                    score,
                    rural_balance
                ))
        
        # 如果有排序，应用排序
        if current_sort:
            col_index = {
                'main_surgery': 0,
                'other_surgery': 1,
                'surgery_count': 2,
                'score': 3,
                'rural_balance': 4
            }[current_sort]
            filtered_items.sort(
                key=lambda x: float(x[col_index]) if isinstance(x[col_index], (int, float)) else x[col_index],
                reverse=current_reverse
            )
        
        # 插入排序后的项目
        for item in filtered_items:
            self.detail_tree.insert(
                '',
                'end',
                values=(
                    item[0],  # 主要手术
                    item[1],  # 其他手术
                    item[2],  # 操作数
                    item[3],  # 分值
                    f"{item[4]:.2f}"  # 城乡盈亏平衡值
                )
            )

    def treeview_sort_column(self, col, reverse):
        """排序Treeview某一列"""
        # 获取所有项目
        l = [(self.detail_tree.set(k, col), k) for k in self.detail_tree.get_children('')]
        
        try:
            # 尝试将值转换为浮点数进行排序
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            # 如果转换失败，按字符串排序
            l.sort(reverse=reverse)
            
        # 重新排序所有项目
        for index, (val, k) in enumerate(l):
            self.detail_tree.move(k, '', index)
            
        # 切换排序方向
        self.detail_tree.heading(col, 
            command=lambda: self.treeview_sort_column(col, not reverse))
        
        # 更新表头显示排序方向
        for c in ('main_surgery', 'other_surgery', 'score', 'rural_balance'):
            if c != col:
                current_text = self.detail_tree.heading(c)['text']
                if '▼' in current_text or '▲' in current_text:
                    self.detail_tree.heading(c, text=current_text.split('▼')[0].split('▲')[0])
        
        # 更新当前列的表头文本，显示排序方向
        current_text = self.detail_tree.heading(col)['text'].split('▼')[0].split('▲')[0]
        self.detail_tree.heading(col, text=f"{current_text}{'▼' if reverse else '▲'}")

    def open_surgery_search(self):
        # 创建手术搜索窗口
        search_window = tk.Toplevel(self.master)
        search_window.title("手术搜索")
        search_window.geometry('1200x600')  # 增加窗口宽度以容纳分值列
        
        # 创建搜索框
        search_frame = tk.Frame(search_window)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="搜索手术:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # 创建结果列表
        result_frame = tk.Frame(search_window)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 修改树形结构，添加分值列
        result_tree = ttk.Treeview(
            result_frame,
            columns=('disease', 'main_surgery', 'other_surgery', 'score', 'rural_balance'),
            show='tree headings',  # 显示树形图标和表头
            height=15
        )
        
        # 设置列
        result_tree.heading('disease', text='病种名称')
        result_tree.heading('main_surgery', text='主要手术')
        result_tree.heading('other_surgery', text='其他手术')
        result_tree.heading('score', text='分值')
        result_tree.heading('rural_balance', text='城乡盈亏平衡值')
        
        # 调整列宽
        result_tree.column('#0', width=50)  # 树形图标列
        result_tree.column('disease', width=180)
        result_tree.column('main_surgery', width=300)
        result_tree.column('other_surgery', width=300)
        result_tree.column('score', width=80, anchor='e')  # 右对齐
        result_tree.column('rural_balance', width=120, anchor='e')  # 右对齐
        
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=result_tree.yview)
        result_tree.configure(yscrollcommand=scrollbar.set)
        
        result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def search_surgery(*args):
            # 清空现有结果
            for item in result_tree.get_children():
                result_tree.delete(item)
            
            search_text = search_var.get().strip().lower()
            if not search_text:
                return
                
            # 搜索匹配的手术
            for group in self.groups:
                main_surgeries = group.main_surgeries_names
                other_surgeries = group.other_surgeries_names
                
                # 检查是否匹配搜索条件
                if any(search_text in surgery.lower() for surgery in main_surgeries) or search_text in other_surgeries.lower():
                    # 创建主要手术的显示文本
                    main_surgery_text = ""
                    for i, surgery in enumerate(main_surgeries, 1):
                        if i > 1:
                            main_surgery_text += " / "
                        main_surgery_text += surgery
                    
                    # 创建其他手术的显示文本
                    other_surgery_text = other_surgeries if other_surgeries else ""
                    
                    # 计算城乡盈亏平衡值
                    is_basic = self.data_handler.is_basic_level_disease(group.disease_name)
                    if is_basic:
                        rural_balance = group.score * self.rural_value
                    else:
                        rural_balance = group.score * self.weight_value * self.rural_value
                    
                    # 插入行
                    parent = result_tree.insert('', 'end', values=(
                        group.disease_name,
                        main_surgery_text,
                        other_surgery_text,
                        f"{group.score:.2f}",  # 添加分值
                        f"{rural_balance:.2f}"  # 添加城乡盈亏平衡值
                    ))
                    
                    # 添加主要手术子项
                    for i, surgery in enumerate(main_surgeries, 1):
                        if search_text in surgery.lower():
                            result_tree.insert(parent, 'end', values=(
                                "",
                                f"{i}. {surgery}",
                                "",
                                "",
                                ""
                            ), tags=('matched',))
                        else:
                            result_tree.insert(parent, 'end', values=(
                                "",
                                f"{i}. {surgery}",
                                "",
                                "",
                                ""
                            ))
                    
                    # 添加其他手术子项
                    if other_surgeries:
                        other_surgeries_list = [s.strip() for s in other_surgeries.split('+')]
                        for i, surgery_group in enumerate(other_surgeries_list, 1):
                            if surgery_group:
                                surgeries = [s.strip() for s in surgery_group.split('/')]
                                for j, surgery in enumerate(surgeries, 1):
                                    if surgery:  # 确保不是空字符串
                                        if search_text in surgery.lower():
                                            result_tree.insert(parent, 'end', values=(
                                                "",
                                                "",
                                                f"{i}.{j} {surgery}",
                                                "",
                                                ""
                                            ), tags=('matched',))
                                        else:
                                            result_tree.insert(parent, 'end', values=(
                                                "",
                                                "",
                                                f"{i}.{j} {surgery}",
                                                "",
                                                ""
                                            ))
                    
                    # 默认展开父节点
                    result_tree.item(parent, open=True)
        
        # 设置匹配项的样式
        result_tree.tag_configure('matched', foreground='red')
        
        # 绑定搜索事件
        search_var.trace('w', search_surgery)
        
        # 双击结果时跳转到对应病种
        def on_double_click(event):
            selection = result_tree.selection()
            if not selection:
                return
                
            # 获取选中项的父节点（如果是子节点）或选中项（如果是父节点）
            item = result_tree.item(selection[0])
            parent = result_tree.parent(selection[0])
            
            # 如果是子节点，使用父节点的病种名称
            if parent:
                disease_name = result_tree.item(parent)['values'][0]
            else:
                disease_name = item['values'][0]
            
            if not disease_name:  # 如果病种名称为空，说明点击的是子项
                disease_name = result_tree.item(parent)['values'][0]
            
            if disease_name:
                # 在主界面选中该病种
                for item in self.disease_tree.get_children():
                    if self.disease_tree.item(item)['values'][1] == disease_name:
                        self.disease_tree.selection_set(item)
                        self.disease_tree.see(item)
                        self.on_select_disease(None)  # 触发选择事件
                        
                        # 查找并选中对应的手术组合
                        main_surgery = result_tree.item(selection[0])['values'][1]
                        other_surgery = result_tree.item(selection[0])['values'][2]
                        
                        # 如果是子项，使用父项的手术信息
                        if not main_surgery and not other_surgery and parent:
                            parent_item = result_tree.item(parent)
                            main_surgery = parent_item['values'][1]
                            other_surgery = parent_item['values'][2]
                        
                        # 在主界面的手术列表中查找并选中对应的手术组合
                        for detail_item in self.detail_tree.get_children():
                            detail_values = self.detail_tree.item(detail_item)['values']
                            if (detail_values[0] == main_surgery and 
                                detail_values[1] == other_surgery):
                                self.detail_tree.selection_set(detail_item)
                                self.detail_tree.see(detail_item)
                                self.on_select_surgery(None)  # 触发手术选择事件
                                break
                        
                        search_window.destroy()  # 关闭搜索窗口
                        break
        
        result_tree.bind('<Double-1>', on_double_click)
        search_entry.focus()

    def sort_disease_list(self, col, reverse):
        """排序病种列表"""
        # 获取所有项目
        items = [(self.disease_tree.set(k, col), k) for k in self.disease_tree.get_children('')]
        
        try:
            # 尝试将值转换为浮点数进行排序
            items.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            # 如果转换失败，按字符串排序
            items.sort(reverse=reverse)
        
        # 重新排序所有项目
        for index, (val, k) in enumerate(items):
            self.disease_tree.move(k, '', index)
        
        # 切换排序方向
        self.disease_tree.heading(col, 
            command=lambda: self.sort_disease_list(col, not reverse))
        
        # 更新表头显示排序方向
        for c in ('standard_score', 'name'):
            if c != col:
                current_text = self.disease_tree.heading(c)['text']
                if '▼' in current_text or '▲' in current_text:
                    self.disease_tree.heading(c, text=current_text.split('▼')[0].split('▲')[0])
        
        # 更新当前列的表头文本，显示排序方向
        current_text = self.disease_tree.heading(col)['text'].split('▼')[0].split('▲')[0]
        self.disease_tree.heading(col, text=f"{current_text}{'▼' if reverse else '▲'}")