class DataHandler:
    def __init__(self):
        # 首先加载手术数据
        from .surgery_data import SURGERY_DATA
        self.surgery_data = SURGERY_DATA
        
        # 初始化其他数据
        self.groups = []
        self.load_data()
    
    def load_data(self):
        # 加载其他数据的代码...
        pass
    
    def get_surgery_number(self, disease_name, main_surgeries, other_surgeries):
        """根据病种名称和手术信息获取序号"""
        for surgery in self.surgery_data:
            if (surgery['病种名称'] == disease_name and 
                surgery['主要手术名称'] == main_surgeries and 
                surgery['其他手术名称'] == other_surgeries):
                return surgery['序号']
        return '-'
    
    def is_basic_level_disease(self, disease_name, main_surgeries=None, other_surgeries=None):
        """
        判断是否为基层病种
        Args:
            disease_name: 病种名称
            main_surgeries: 主要手术名称（可选）
            other_surgeries: 次要手术名称（可选）
        Returns:
            bool: 是否为基层病种
        """
        # 如果提供了具体手术信息，则按手术组合判断
        if main_surgeries is not None:
            for surgery in self.surgery_data:
                if (surgery['病种名称'] == disease_name and 
                    surgery['主要手术名称'] == main_surgeries and 
                    surgery['其他手术名称'] == other_surgeries):
                    # 检查备注字段是否包含"基层病种"
                    remark = surgery.get('备注', '')
                    return '基层病种' in remark if remark else False
            return False
        
        # 如果只提供病种名称，则检查该病种下是否有基层病种
        for surgery in self.surgery_data:
            if surgery['病种名称'] == disease_name:
                remark = surgery.get('备注', '')
                if remark and '基层病种' in remark:
                    return True
        return False