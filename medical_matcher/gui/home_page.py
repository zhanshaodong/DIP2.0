import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .main_window import MainWindow
import pandas as pd
import json

class HomePage(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.matcher_window = None
        self.matcher_app = None
        
        # 从文件加载上次保存的参数
        self.load_params()
        self.create_widgets()
        
    def load_params(self):
        """从文件加载参数"""
        try:
            with open('params.json', 'r') as f:
                params = json.load(f)
                self.last_rural = params.get('rural_urban', '1.0')
                self.last_worker = params.get('worker', '1.0')
                self.last_weight = params.get('weight', '1.0')
        except:
            # 如果文件不存在或读取失败，使用默认值
            self.last_rural = '1.0'
            self.last_worker = '1.0'
            self.last_weight = '1.0'
    
    def save_params(self):
        """保存参数到文件"""
        params = {
            'rural_urban': self.rural_urban_value.get(),
            'worker': self.worker_value.get(),
            'weight': self.weight_value.get()
        }
        try:
            with open('params.json', 'w') as f:
                json.dump(params, f)
            messagebox.showinfo("成功", "参数已保存！")
        except Exception as e:
            messagebox.showerror("错误", f"保存参数失败：{str(e)}")
    
    def create_widgets(self):
        # 创建参数配置区
        param_frame = ttk.LabelFrame(self, text="参数配置", padding="10")
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 参数输入区
        input_frame = ttk.Frame(param_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        # 城乡分值配置
        ttk.Label(input_frame, text="城乡分值:").grid(row=0, column=0, padx=5, pady=5)
        self.rural_urban_value = ttk.Entry(input_frame, width=10)
        self.rural_urban_value.grid(row=0, column=1, padx=5, pady=5)
        self.rural_urban_value.insert(0, self.last_rural)
        self.rural_urban_value.bind('<KeyRelease>', self.on_param_change)
        
        # 职工分值配置
        ttk.Label(input_frame, text="职工分值:").grid(row=0, column=2, padx=5, pady=5)
        self.worker_value = ttk.Entry(input_frame, width=10)
        self.worker_value.grid(row=0, column=3, padx=5, pady=5)
        self.worker_value.insert(0, self.last_worker)
        self.worker_value.bind('<KeyRelease>', self.on_param_change)
        
        # 权重系数配置
        ttk.Label(input_frame, text="权重系数:").grid(row=0, column=4, padx=5, pady=5)
        self.weight_value = ttk.Entry(input_frame, width=10)
        self.weight_value.grid(row=0, column=5, padx=5, pady=5)
        self.weight_value.insert(0, self.last_weight)
        self.weight_value.bind('<KeyRelease>', self.on_param_change)
        
        # 按钮区
        button_frame = ttk.Frame(param_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # 更新按钮
        ttk.Button(button_frame, text="手动更新参数", 
                  command=self.update_params).pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        ttk.Button(button_frame, text="退出保存参数", 
                  command=self.save_params).pack(side=tk.LEFT, padx=5)
        
        # 导入按钮
        ttk.Button(button_frame, text="导入月度参数", 
                  command=self.import_params).pack(side=tk.LEFT, padx=5)
        
        # 导出模板按钮
        ttk.Button(button_frame, text="导出月度模板", 
                  command=self.export_template).pack(side=tk.LEFT, padx=5)
        
        # 添加查看月度参数按钮
        ttk.Button(button_frame, text="查看月度参数", 
                  command=lambda: self.show_monthly_params() if hasattr(self, 'monthly_params') else 
                          messagebox.showinfo("提示", "请先导入月度参数！")
                  ).pack(side=tk.LEFT, padx=5)
        
        # 功能区
        func_frame = ttk.LabelFrame(self, text="功能区", padding="10")
        func_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # DIP2.0按钮
        ttk.Button(func_frame, text="DIP2.0", 
                  command=self.open_matcher).pack(pady=10)
        
        # 预留其他功能按钮
        ttk.Button(func_frame, text="科室盈亏", 
                  state="disabled").pack(pady=10)
        ttk.Button(func_frame, text="数据分析", 
                  state="disabled").pack(pady=10)
        
    def update_params(self):
        # 获取并更新参数值
        try:
            rural_urban = float(self.rural_urban_value.get())
            worker = float(self.worker_value.get())
            weight = float(self.weight_value.get())
            
            # 检查matcher_app是否存在且窗口是否有效
            if self.matcher_app and self.matcher_window.winfo_exists():
                self.matcher_app.update_params_from_home(rural_urban, worker, weight)
                messagebox.showinfo("成功", "参数更新成功！")
            else:
                # 如果窗口不存在，清除引用
                self.matcher_app = None
                self.matcher_window = None
                messagebox.showinfo("成功", "参数已更新，但只对当前窗口生效！")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值！")
    
    def import_params(self):
        """导入Excel参数"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            if file_path:
                df = pd.read_excel(file_path)
                self.monthly_params = df  # 保存月度参数
                self.show_monthly_params()  # 显示月度参数窗口
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")
    
    def update_params_from_matcher(self, rural_urban, worker, weight):
        """从匹配系统更新参数到首页"""
        self.rural_urban_value.delete(0, tk.END)
        self.rural_urban_value.insert(0, str(rural_urban))
        
        self.worker_value.delete(0, tk.END)
        self.worker_value.insert(0, str(worker))
        
        self.weight_value.delete(0, tk.END)
        self.weight_value.insert(0, str(weight))
    
    def open_matcher(self):
        # 打开手术匹配系统窗口
        self.matcher_window = tk.Toplevel(self.master)
        self.matcher_window.title("手术匹配系统")
        self.matcher_window.geometry("800x600")
        self.matcher_app = MainWindow(
            master=self.matcher_window,
            home_page=self  # 传递首页实例以实现参数同步
        )
        self.matcher_app.pack(fill=tk.BOTH, expand=True) 
    
    def on_param_change(self, event=None):
        """当参数值改变时调用"""
        try:
            rural_urban = float(self.rural_urban_value.get())
            worker = float(self.worker_value.get())
            weight = float(self.weight_value.get())
            
            # 检查matcher_app是否存在且窗口是否有效
            if self.matcher_app and self.matcher_window.winfo_exists():
                self.matcher_app.update_params_from_home(rural_urban, worker, weight)
        except ValueError:
            pass  # 输入非数字时不进行更新 
    
    def export_template(self):
        """导出Excel模板文件"""
        try:
            # 创建12个月的示例数据
            months = [f"{i}月" for i in range(1, 13)]
            template_data = {
                "月份": months,
                "城乡分值": [8.0] * 12,  # 12个月的示例值
                "职工分值": [10.0] * 12
            }
            df = pd.DataFrame(template_data)
            
            # 让用户选择保存位置
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile="月度参数模板.xlsx"
            )
            
            if file_path:
                # 保存Excel文件
                df.to_excel(file_path, index=False)
                messagebox.showinfo("成功", "模板文件已导出！")
                
                # 询问是否打开文件
                if messagebox.askyesno("提示", "是否打开模板文件？"):
                    import os
                    os.startfile(file_path)
                    
        except Exception as e:
            messagebox.showerror("错误", f"导出模板失败：{str(e)}")
    
    def show_monthly_params(self):
        """显示月度参数表格"""
        # 创建新窗口
        params_window = tk.Toplevel(self.master)
        params_window.title("月度参数表")
        params_window.geometry("600x400")
        
        # 创建表格
        tree_frame = ttk.Frame(params_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建Treeview
        tree = ttk.Treeview(tree_frame, columns=("month", "rural", "worker"), show="headings")
        
        # 设置列标题
        tree.heading("month", text="月份")
        tree.heading("rural", text="城乡分值")
        tree.heading("worker", text="职工分值")
        
        # 设置列宽
        tree.column("month", width=100)
        tree.column("rural", width=200)
        tree.column("worker", width=200)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 填充数据
        for _, row in self.monthly_params.iterrows():
            tree.insert("", tk.END, values=(row["月份"], row["城乡分值"], row["职工分值"]))
        
        # 布局
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加应用按钮
        def apply_month():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                values = item['values']
                # 更新当前参数值
                self.rural_urban_value.delete(0, tk.END)
                self.rural_urban_value.insert(0, str(values[1]))
                self.worker_value.delete(0, tk.END)
                self.worker_value.insert(0, str(values[2]))
                # 触发参数更新
                self.update_params()
        
        button_frame = ttk.Frame(params_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="应用选中月份参数", command=apply_month).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=params_window.destroy).pack(side=tk.RIGHT, padx=5) 