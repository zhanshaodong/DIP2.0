import pandas as pd
import matplotlib.pyplot as plt
from data.surgery_data import SURGERY_DATA
from models.disease_group import DiseaseGroup

class DataHandler:
    def __init__(self):
        self.groups = self._load_predefined_data()
    
    def _load_predefined_data(self):
        """加载预定义的数据"""
        return [DiseaseGroup.from_row(row) for row in SURGERY_DATA]
    
    def load_data(self, file_path=None):
        """保留文件加载方法，但默认使用预定义数据"""
        if file_path:
            df = pd.read_excel(file_path, engine='openpyxl')
            return [DiseaseGroup.from_row(row) for _, row in df.iterrows()]
        return self.groups

    @staticmethod
    def match_group(user_input, groups):
        matches = []
        user_main_surgery = user_input.get('main_surgery', '').strip().split('/')
        user_other_surgeries = set(user_input.get('other_surgeries', '').strip().split('/'))
        
        for group in groups:
            if all(ms in group.main_surgeries for ms in user_main_surgery):
                matched_other_surgeries = set(group.other_surgeries) & user_other_surgeries
                if matched_other_surgeries:
                    matches.append((group, len(matched_other_surgeries)))
        
        matches.sort(key=lambda x: (x[1], x[0].score), reverse=True)
        return matches[0][0] if matches else None

    @staticmethod
    def visualize_scores(disease_group):
        plt.figure(figsize=(8, 6))
        plt.bar([disease_group.disease_type], [disease_group.score])
        plt.xlabel('病种类型')
        plt.ylabel('分值')
        plt.title('病种分值展示')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show() 

    def is_basic_level_disease(self, disease_name):
        """判断是否为基层病种"""
        # 从预定义数据中判断是否为基层病种
        for group in self.groups:
            if group.disease_name == disease_name:
                return getattr(group, 'is_basic_level', False)
        return False