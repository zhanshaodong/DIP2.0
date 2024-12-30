import tkinter as tk
from gui.home_page import HomePage

def main():
    root = tk.Tk()
    root.title("医疗系统")
    # 增加窗口默认大小以显示完整内容
    root.geometry("1400x800")  # 修改为更大的尺寸
    
    # 设置最小窗口大小，防止用户将窗口调整得太小
    root.minsize(1200, 700)
    
    app = HomePage(master=root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()

if __name__ == "__main__":
    main() 