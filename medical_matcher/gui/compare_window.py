import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from matplotlib.font_manager import FontProperties

class CompareWindow(tk.Toplevel):
    def __init__(self, master, data_handler):
        super().__init__(master)
        self.title("病种分值对比")
        self.geometry("1200x800")
        self.data_handler = data_handler
        
        # 设置中文字体
        self.font = FontProperties(family=['Heiti TC', 'Arial Unicode MS', 'Microsoft YaHei', 'SimHei'])
        
        # 设置窗口背景色
        self.configure(bg='#2b2b2b')
        
        # 创建左右分栏
        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg='#2b2b2b')
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧病种选择区域
        self.left_frame = tk.Frame(self.paned, width=300, bg='#2b2b2b')
        self.paned.add(self.left_frame)
        
        # 右侧图表区域
        self.right_frame = tk.Frame(self.paned, bg='#2b2b2b')
        self.paned.add(self.right_frame)
        
        # 创建左侧组件
        self.create_left_panel()
        
        # 创建右侧图表
        self.create_chart_area()
        
        # 添加选中病种列表
        self.selected_diseases = []
        
    def create_left_panel(self):
        """创建左侧面板"""
        # 搜索框
        search_frame = tk.Frame(self.left_frame, bg='#2b2b2b')
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            search_frame, 
            text="搜索病种:", 
            bg='#2b2b2b',
            fg='white'
        ).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_disease_list)
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg='#333333',
            fg='white',
            insertbackground='white'
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 病种列表
        list_frame = tk.Frame(self.left_frame, bg='#2b2b2b')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 配置Treeview样式
        style = ttk.Style()
        style.configure(
            "Custom.Treeview",
            background='#333333',
            foreground='white',
            fieldbackground='#333333'
        )
        style.configure(
            "Custom.Treeview.Heading",
            background='#333333',
            foreground='white'
        )
        
        self.disease_list = ttk.Treeview(
            list_frame,
            columns=('name',),
            show='headings',
            selectmode='extended',
            style="Custom.Treeview"
        )
        self.disease_list.heading('name', text='病种名称')
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.disease_list.yview
        )
        self.disease_list.configure(yscrollcommand=scrollbar.set)
        
        self.disease_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.disease_list.bind('<<TreeviewSelect>>', self.on_select_disease)
        
        # 初始化病种列表
        self.update_disease_list()
        
    def create_chart_area(self):
        """创建右侧卡片区域"""
        # 卡片区域
        cards_outer_frame = tk.Frame(self.right_frame, bg='#2b2b2b')
        cards_outer_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        tk.Label(
            cards_outer_frame,
            text="已选病种:",
            bg='#2b2b2b',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack(anchor='w', padx=5, pady=5)
        
        # 创建卡片容器（使用Canvas和Frame的组合实现滚动）
        self.cards_canvas = tk.Canvas(
            cards_outer_frame,
            bg='#2b2b2b',
            highlightthickness=0
        )
        self.cards_canvas.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # 创建放置卡片的框架
        self.cards_frame = tk.Frame(self.cards_canvas, bg='#2b2b2b')
        
        # 添加水平滚动条
        h_scrollbar = ttk.Scrollbar(
            cards_outer_frame,
            orient=tk.HORIZONTAL,
            command=self.cards_canvas.xview
        )
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 添加垂直滚动条
        v_scrollbar = ttk.Scrollbar(
            cards_outer_frame,
            orient=tk.VERTICAL,
            command=self.cards_canvas.yview
        )
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置Canvas
        self.cards_canvas.configure(
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        
        # 创建放置卡片的框架
        self.cards_canvas.create_window((0, 0), window=self.cards_frame, anchor='nw')
        
        # 绑定调整大小事件
        self.cards_frame.bind('<Configure>', self._on_frame_configure)
        self.cards_canvas.bind('<Configure>', self._on_canvas_configure)
        
        # 添加控制按钮
        button_frame = tk.Frame(cards_outer_frame, bg='#2b2b2b')
        button_frame.pack(fill=tk.X, pady=5, padx=5)
        
        clear_button = tk.Button(
            button_frame,
            text="清空所有",
            command=self.clear_selected
        )
        clear_button.pack(side=tk.RIGHT)

    def _on_frame_configure(self, event=None):
        """处理内部框架大小变化"""
        self.cards_canvas.configure(scrollregion=self.cards_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """处理画布大小变化"""
        # 获取当前画布宽度
        canvas_width = event.width
        # 重新设置内部框架宽度
        self.cards_canvas.itemconfig(self.cards_canvas.find_withtag("all")[0], width=canvas_width)

    def update_disease_list(self):
        """更新病种列表"""
        # 清空列表
        for item in self.disease_list.get_children():
            self.disease_list.delete(item)
        
        # 获取所有不重复的病种
        diseases = set()
        for group in self.data_handler.groups:
            diseases.add(group.disease_name)
        
        # 添加到列表
        for disease in sorted(diseases):
            self.disease_list.insert('', 'end', values=(disease,))
            
    def filter_disease_list(self, *args):
        """过滤病种列表"""
        search_text = self.search_var.get().lower()
        
        # 清空列表
        for item in self.disease_list.get_children():
            self.disease_list.delete(item)
        
        # 重新添加匹配的病种
        diseases = set()
        for group in self.data_handler.groups:
            if search_text in group.disease_name.lower():
                diseases.add(group.disease_name)
        
        for disease in sorted(diseases):
            self.disease_list.insert('', 'end', values=(disease,))
            
    def create_disease_card(self, disease_name, base_score, rural_balance, worker_balance):
        """创建病种卡片"""
        # 创建一行作为卡片容器
        card = tk.Frame(
            self.cards_frame,
            bg='#333333',
            relief=tk.RAISED,
            bd=1
        )
        card.pack(fill=tk.X, padx=5, pady=2)
        
        # 使用Grid布局管理器，分配列宽
        card.grid_columnconfigure(0, weight=1)  # 病种名称区域
        card.grid_columnconfigure(1, weight=1)  # 数值信息区域
        card.grid_columnconfigure(2, minsize=50)  # 删除按钮列
        
        # 病种名称（左侧）
        name_label = tk.Label(
            card,
            text=disease_name,
            bg='#333333',
            fg='white',
            font=('Arial', 14, 'bold'),
            anchor='w',
            justify=tk.LEFT,
            padx=20
        )
        name_label.grid(row=0, column=0, sticky='w', pady=10)
        
        # 数值信息区域（右侧）
        info_frame = tk.Frame(card, bg='#333333')
        info_frame.grid(row=0, column=1, sticky='e', padx=10)
        
        # 基准分值
        score_frame = tk.Frame(info_frame, bg='#333333')
        score_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            score_frame,
            text="基准分值",
            bg='#333333',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack()
        
        tk.Label(
            score_frame,
            text=f"{base_score:.0f}",
            bg='#333333',
            fg='#2196F3',
            font=('Arial', 16, 'bold'),
            width=6,
            anchor='e'
        ).pack()
        
        # 城乡盈亏平衡值
        rural_frame = tk.Frame(info_frame, bg='#333333')
        rural_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            rural_frame,
            text="城乡盈亏平衡值",
            bg='#333333',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack()
        
        tk.Label(
            rural_frame,
            text=f"¥{rural_balance:.2f}",
            bg='#333333',
            fg='#4CAF50',
            font=('Arial', 16, 'bold'),
            width=12,
            anchor='e'
        ).pack()
        
        # 职工盈亏平衡值
        worker_frame = tk.Frame(info_frame, bg='#333333')
        worker_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            worker_frame,
            text="职工盈亏平衡值",
            bg='#333333',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack()
        
        tk.Label(
            worker_frame,
            text=f"¥{worker_balance:.2f}",
            bg='#333333',
            fg='#4CAF50',
            font=('Arial', 16, 'bold'),
            width=12,
            anchor='e'
        ).pack()
        
        # 删除按钮
        delete_btn = tk.Label(
            card,
            text="✕",
            bg='#333333',
            fg='#666666',
            font=('Arial', 12),
            cursor='hand2',
            width=2
        )
        delete_btn.grid(row=0, column=2, padx=5, sticky='ns')
        
        # 添加鼠标悬停效果
        def on_enter(e):
            delete_btn.configure(fg='#FF4444')
        
        def on_leave(e):
            delete_btn.configure(fg='#666666')
        
        def on_click(e):
            self.remove_disease_card(card, disease_name)
        
        delete_btn.bind('<Enter>', on_enter)
        delete_btn.bind('<Leave>', on_leave)
        delete_btn.bind('<Button-1>', on_click)
        
        return card

    def remove_disease_card(self, card, disease_name):
        """移除单个病种卡片"""
        card.destroy()
        self.selected_diseases.remove(disease_name)
        self.update_chart(self.selected_diseases)

    def clear_selected(self):
        """清空所有已选病种"""
        # 清空所有卡片
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        self.selected_diseases.clear()
        self.update_chart([])

    def on_select_disease(self, event):
        """处理病种选择事件"""
        selection = self.disease_list.selection()
        if not selection:
            return
            
        # 获取选中的病种
        for item in selection:
            disease_name = self.disease_list.item(item)['values'][0]
            if disease_name not in self.selected_diseases:
                # 获取病种基准分值和盈亏平衡值
                base_score = 0
                conservative_score = None
                min_score = float('inf')
                
                for group in self.data_handler.groups:
                    if group.disease_name == disease_name:
                        if group.score < min_score:
                            min_score = group.score
                        # 检查是否是保守治疗
                        main_surgeries = ' / '.join(group.main_surgeries_names).lower()
                        if '保守治疗' in main_surgeries:
                            conservative_score = group.score
                            break
                
                # 使用保守治疗分值或最低分值
                base_score = conservative_score if conservative_score is not None else min_score
                
                # 计算盈亏平衡值
                is_basic = self.data_handler.is_basic_level_disease(disease_name)
                if is_basic:
                    rural_balance = base_score * 8
                    worker_balance = base_score * 10
                else:
                    rural_balance = base_score * 0.889 * 8
                    worker_balance = base_score * 0.889 * 10
                
                # 创建新卡片
                self.create_disease_card(disease_name, base_score, rural_balance, worker_balance)
                self.selected_diseases.append(disease_name)
                
                # 重新排序所有卡片
                self.sort_disease_cards()
        
        # 更新图表
        self.update_chart(self.selected_diseases)

    def sort_disease_cards(self):
        """对疾病卡片按分值从高到低排序并显示差额"""
        # 获取所有卡片及其分值
        cards_data = []
        for card in self.cards_frame.winfo_children():
            try:
                # 获取分值标签
                score_frame = card.winfo_children()[1].winfo_children()[0]  # right_area -> score_frame
                score_label = score_frame.winfo_children()[1]  # 第二个label是分值
                score = float(score_label.cget('text'))
                cards_data.append((card, score))
            except (IndexError, ValueError, AttributeError):
                continue
        
        # 按分值排序
        cards_data.sort(key=lambda x: x[1], reverse=True)
        
        # 重新排列卡片并添加差额显示
        prev_score = None
        for i, (card, score) in enumerate(cards_data):
            card.pack_forget()
            
            # 如果不是第一个卡片，显示与上一个分值的差额
            if prev_score is not None:
                diff = prev_score - score
                if diff > 0:
                    # 创建差额显示框架
                    diff_frame = tk.Frame(self.cards_frame, bg='#2b2b2b', height=30)
                    diff_frame.pack(fill=tk.X, padx=5)
                    diff_frame.pack_propagate(False)
                    
                    # 显示差额
                    tk.Label(
                        diff_frame,
                        text=f"↓ {diff:.0f}",
                        bg='#2b2b2b',
                        fg='#FF4444',
                        font=('Arial', 12)
                    ).pack(side=tk.RIGHT, padx=20)
            
            # 显示卡片
            card.pack(fill=tk.X, padx=5, pady=2)
            prev_score = score

    def update_chart(self, diseases):
        """更新卡片显示"""
        # 清空所有现有卡片
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        
        # 收集数据并创建卡片
        for disease in diseases:
            # 获取该病种的基准分值
            conservative_score = None
            min_score = float('inf')
            
            for group in self.data_handler.groups:
                if group.disease_name == disease:
                    if group.score < min_score:
                        min_score = group.score
                    # 检查是否是保守治疗
                    main_surgeries = ' / '.join(group.main_surgeries_names).lower()
                    if '保守治疗' in main_surgeries:
                        conservative_score = group.score
                        break
            
            # 使用保守治疗分值或最低分值
            base_score = conservative_score if conservative_score is not None else min_score
            
            # 计算盈亏平衡值
            is_basic = self.data_handler.is_basic_level_disease(disease)
            if is_basic:
                rural_balance = base_score * 8
                worker_balance = base_score * 10
            else:
                rural_balance = base_score * 0.889 * 8
                worker_balance = base_score * 0.889 * 10
            
            # 创建卡片
            self.create_disease_card(disease, base_score, rural_balance, worker_balance)
        
        # 排序卡片
        self.sort_disease_cards()
 