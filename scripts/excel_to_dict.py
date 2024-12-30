import pandas as pd
import os
from tkinter import filedialog
import tkinter as tk

def convert_excel_to_dict():
    # 创建临时的 root 窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 打开文件选择对话框
    excel_file = filedialog.askopenfilename(
        title="选择Excel文件",
        filetypes=[("Excel files", "*.xlsx")]
    )
    
    if not excel_file:
        print("未选择文件")
        return
    
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file)
        
        # 获取输出路径
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'medical_matcher', 'data', 'surgery_data.py'
        )
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入数据
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 预定义的手术数据\n")
            f.write("SURGERY_DATA = [\n")
            
            for _, row in df.iterrows():
                f.write("    {\n")
                for column in df.columns:
                    value = row[column]
                    if pd.isna(value):
                        value = ""
                    if isinstance(value, str):
                        f.write(f'        "{column}": "{value}",\n')
                    else:
                        f.write(f'        "{column}": {value},\n')
                f.write("    },\n")
            
            f.write("]\n")
        
        print(f"数据已成功写入到 {output_path}")
        
    except Exception as e:
        print(f"发生错误：{str(e)}")

if __name__ == "__main__":
    convert_excel_to_dict() 