#!/usr/bin/env python3
"""
修复后的MPC场景运行程序
确保正确的输入数据格式并显示reveal的输出结果
"""

import os
import sys
import subprocess
import logging
import numpy as np
from pathlib import Path
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixedMPCScenarios:
    """修复后的MPC场景执行器"""
    
    def __init__(self, mp_spdz_path="/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        self.mp_spdz_path = Path(mp_spdz_path)
        
    def generate_financial_input_data(self, n_parties=3, data_size=100):
        """生成金融场景的正确输入数据"""
        
        logger.info(f"生成金融数据: {n_parties}方, 每方{data_size}数据点")
        
        np.random.seed(42)  # 确保可重复结果
        
        # 为每个参与方生成数据
        banks = ["Citibank", "JP Morgan", "Bank of America"]
        party_data = {}
        
        for party_id in range(n_parties):
            # 每个银行有不同的基础特征
            base_credit = 720 + party_id * 15
            base_income = 45000 + party_id * 10000
            
            # X变量: 信用评分 
            credit_scores = np.random.normal(base_credit, 60, data_size)
            credit_scores = np.clip(credit_scores, 300, 850)
            
            # Y变量: 年收入
            incomes = np.random.normal(base_income, 15000, data_size)
            incomes = np.clip(incomes, 20000, 150000)
            
            party_data[party_id] = {
                'bank_name': banks[party_id],
                'credit_scores': credit_scores,
                'incomes': incomes
            }
            
            # 创建MP-SPDZ输入文件
            input_file = self.mp_spdz_path / f"Player-Data/Input-P{party_id}-0"
            with open(input_file, 'w') as f:
                # 先写入X变量的所有值
                for score in credit_scores:
                    f.write(f"{score:.2f}\\n")
                # 再写入Y变量的所有值
                for income in incomes:
                    f.write(f"{income:.0f}\\n")
            
            logger.info(f"Generated data for {banks[party_id]}: {data_size} customers")
        
        return party_data
    
    def generate_medical_input_data(self, n_parties=3, data_size=100):
        """生成医疗场景的正确输入数据"""
        
        logger.info(f"生成医疗数据: {n_parties}方, 每方{data_size}数据点")
        
        np.random.seed(123)  # 不同的种子用于医疗数据
        
        # 医疗机构
        hospitals = ["General Hospital", "Research Medical Center", "University Hospital"]
        party_data = {}
        
        for party_id in range(n_parties):
            # X变量: 患者年龄
            base_age = 55 + party_id * 5
            ages = np.random.normal(base_age, 15, data_size)
            ages = np.clip(ages, 18, 90)
            
            # Y变量: 治疗效果评分 (0-100)
            base_effectiveness = 75 - party_id * 5  # 不同医院的治疗效果
            effectiveness = np.random.normal(base_effectiveness, 20, data_size)
            effectiveness = np.clip(effectiveness, 0, 100)
            
            party_data[party_id] = {
                'hospital_name': hospitals[party_id],
                'ages': ages,
                'effectiveness': effectiveness
            }
            
            # 创建MP-SPDZ输入文件
            input_file = self.mp_spdz_path / f"Player-Data/Input-P{party_id}-0"
            with open(input_file, 'w') as f:
                # 先写入X变量的所有值
                for age in ages:
                    f.write(f"{age:.1f}\\n")
                # 再写入Y变量的所有值  
                for eff in effectiveness:
                    f.write(f"{eff:.1f}\\n")
            
            logger.info(f"Generated data for {hospitals[party_id]}: {data_size} patients")
        
        return party_data
    
    def run_mpc_program_with_output(self, program_name, scenario_name):
        """运行MPC程序并捕获完整输出"""
        
        logger.info(f"运行MPC程序: {program_name} ({scenario_name})")
        
        try:
            os.chdir(self.mp_spdz_path)
            
            # 使用emulate.x运行程序并捕获所有输出
            result = subprocess.run(
                ["./emulate.x", program_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("MPC程序执行成功")
                
                # 检查是否有输出
                output = result.stdout + result.stderr
                if output.strip():
                    return True, output
                else:
                    logger.warning("程序执行成功但没有输出")
                    return True, "程序执行成功，但没有捕获到输出"
            else:
                logger.error(f"MPC程序执行失败: {result.returncode}")
                logger.error(f"错误输出: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            logger.error("MPC程序执行超时")
            return False, "执行超时"
        except Exception as e:
            logger.error(f"MPC程序执行异常: {e}")
            return False, str(e)
    
    def extract_business_insights(self, output_text, scenario_name):
        """从MPC输出中提取业务洞察"""
        
        logger.info(f"提取{scenario_name}的业务洞察")
        
        insights = {
            'scenario': scenario_name,
            'disclosed_data': {},
            'raw_output': output_text
        }
        
        # 查找BUSINESS_DISCLOSURE行
        lines = output_text.split('\\n')
        disclosure_lines = [line for line in lines if 'BUSINESS_DISCLOSURE' in line]
        
        logger.info(f"发现 {len(disclosure_lines)} 行业务披露数据")
        
        for line in disclosure_lines:
            logger.info(f"处理披露行: {line}")
            
            # 解析不同类型的披露数据
            import re
            
            if "Mean X:" in line:
                match = re.search(r'Mean X:\\s*([-\\d.]+)', line)
                if match:
                    insights['disclosed_data']['mean_x'] = float(match.group(1))
            
            elif "Mean Y:" in line:
                match = re.search(r'Mean Y:\\s*([-\\d.]+)', line)
                if match:
                    insights['disclosed_data']['mean_y'] = float(match.group(1))
            
            elif "Variance X:" in line:
                match = re.search(r'Variance X:\\s*([-\\d.]+)', line)
                if match:
                    insights['disclosed_data']['variance_x'] = float(match.group(1))
            
            elif "Std Dev X:" in line:
                match = re.search(r'Std Dev X:\\s*([-\\d.]+)', line)
                if match:
                    insights['disclosed_data']['std_dev_x'] = float(match.group(1))
            
            elif "Correlation X-Y:" in line:
                match = re.search(r'Correlation X-Y:\\s*([-\\d.]+)', line)
                if match:
                    insights['disclosed_data']['correlation'] = float(match.group(1))
        
        return insights
    
    def display_scenario_results(self, scenario_name, party_data, insights):
        """显示场景结果"""
        
        print("\\n" + "="*80)
        print(f"🔐 {scenario_name.upper()} MPC场景结果")
        print("="*80)
        
        # 显示输入数据摘要（私有数据，实际MPC中不会暴露）
        print(f"\\n📊 输入数据摘要 (私有数据 - 仅用于验证):")
        print("-"*60)
        
        for party_id, data in party_data.items():
            if scenario_name == "financial":
                name = data.get('bank_name', f'Party {party_id}')
                mean_credit = np.mean(data['credit_scores']) if 'credit_scores' in data else 0
                mean_income = np.mean(data['incomes']) if 'incomes' in data else 0
                print(f"{name}: 平均信用评分={mean_credit:.1f}, 平均收入=${mean_income:.0f}")
            else:
                name = data.get('hospital_name', f'Party {party_id}')
                mean_age = np.mean(data['ages']) if 'ages' in data else 0
                mean_eff = np.mean(data['effectiveness']) if 'effectiveness' in data else 0
                print(f"{name}: 平均年龄={mean_age:.1f}, 平均效果={mean_eff:.1f}")
        
        # 显示MPC披露的数据
        print(f"\\n🔓 MPC披露的聚合统计 (业务洞察):")
        print("-"*60)
        
        disclosed = insights.get('disclosed_data', {})
        if disclosed:
            for key, value in disclosed.items():
                readable_name = key.replace('_', ' ').title()
                if scenario_name == "financial":
                    if 'mean_x' in key:
                        readable_name = "平均信用评分"
                    elif 'mean_y' in key:
                        readable_name = "平均年收入"
                else:
                    if 'mean_x' in key:
                        readable_name = "平均患者年龄"
                    elif 'mean_y' in key:
                        readable_name = "平均治疗效果"
                
                print(f"📈 {readable_name}: {value:.6f}")
        else:
            print("❌ 未找到MPC披露数据")
        
        # 显示原始输出
        print(f"\\n📋 MPC程序原始输出:")
        print("-"*60)
        raw_output = insights.get('raw_output', '无输出')
        print(raw_output)
        
        print(f"\\n✅ 隐私保证:")
        print("-"*60)
        print("✓ 各方原始数据从未暴露给其他参与方")
        print("✓ 只有聚合统计结果通过reveal机制披露")
        print("✓ 符合隐私保护的多方计算要求")

def main():
    """主函数"""
    
    print("🚀 启动修复后的MPC场景演示")
    print("="*80)
    
    runner = FixedMPCScenarios()
    
    # 测试金融场景
    print("\\n🏦 运行金融风险评估场景...")
    try:
        # 1. 生成金融数据
        financial_data = runner.generate_financial_input_data()
        
        # 2. 运行joint_statistics程序
        success, output = runner.run_mpc_program_with_output("joint_statistics", "financial")
        
        if success:
            # 3. 提取业务洞察
            insights = runner.extract_business_insights(output, "financial")
            
            # 4. 显示结果
            runner.display_scenario_results("financial", financial_data, insights)
        else:
            print(f"❌ 金融场景执行失败: {output}")
    
    except Exception as e:
        print(f"❌ 金融场景异常: {e}")
    
    # 测试医疗场景
    print("\\n\\n🏥 运行医疗研究场景...")
    try:
        # 1. 生成医疗数据
        medical_data = runner.generate_medical_input_data()
        
        # 2. 运行joint_statistics程序
        success, output = runner.run_mpc_program_with_output("joint_statistics", "medical")
        
        if success:
            # 3. 提取业务洞察
            insights = runner.extract_business_insights(output, "medical")
            
            # 4. 显示结果
            runner.display_scenario_results("medical", medical_data, insights)
        else:
            print(f"❌ 医疗场景执行失败: {output}")
    
    except Exception as e:
        print(f"❌ 医疗场景异常: {e}")
    
    print("\\n" + "="*80)
    print("🎉 MPC场景演示完成!")
    print("="*80)

if __name__ == "__main__":
    main()