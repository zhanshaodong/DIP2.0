class DiseaseGroup:
    def __init__(self, dip_code, main_surgeries, main_surgeries_names, other_surgeries, 
                 other_surgeries_names, score, disease_name, remark=''):
        self.dip_code = dip_code
        self.main_surgeries = main_surgeries
        self.main_surgeries_names = main_surgeries_names
        self.other_surgeries = other_surgeries
        self.other_surgeries_names = other_surgeries_names
        self.score = score
        self.disease_name = disease_name
        self.remark = remark
        self.is_basic_level = '基层病种' in (remark or '')

    @classmethod
    def from_row(cls, row):
        dip_code = row['DIP分组编码']
        disease_name = row['病种名称']
        
        # 主要手术
        main_surgery = str(row['主要手术编码']).replace('nan', '')
        main_surgery_name = str(row['主要手术名称']).replace('nan', '')
        
        # 其他手术
        other_surgeries = str(row['其他手术编码']).replace('nan', '')
        other_surgeries_name = str(row['其他手术名称']).replace('nan', '')
        
        # 获取备注信息
        remark = str(row.get('备注', '')).replace('nan', '')
        
        # 如果有多个手术组，确保+号前后的空格处理正确
        if other_surgeries_name:
            other_surgeries_name = ' + '.join(
                part.strip() 
                for part in other_surgeries_name.split('+')
            )
        
        # 处理主要手术代码和名称
        main_surgeries_list = [s.strip() for s in main_surgery.split('/') if s]
        main_surgeries_names_list = [s.strip() for s in main_surgery_name.split('/') if s]
        
        # 处理其他手术代码
        other_surgeries_list = [s.strip() for s in other_surgeries.split('/') if s]
        
        # 如果主要手术和其他手术都为空，则设置为保守治疗
        if not main_surgeries_list and not other_surgeries_list:
            main_surgeries_names_list = ["保守治疗"]
        
        return cls(
            dip_code=dip_code,
            main_surgeries=main_surgeries_list,
            main_surgeries_names=main_surgeries_names_list,
            other_surgeries=other_surgeries_list,
            other_surgeries_names=other_surgeries_name,
            score=row['分值'],
            disease_name=disease_name,
            remark=remark
        ) 