#!/usr/bin/env python3
"""
真正的MPC数据生成器
为MP-SPDZ协议生成各参与方的私有输入数据
"""

import numpy as np
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class MPCDataGenerator:
    """MP-SPDZ真实协议数据生成器"""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        np.random.seed(seed)
    
    def generate_financial_mpc_data(self, n_parties: int = 3, customers_per_bank: int = 100) -> Dict[int, Dict]:
        """
        为金融MPC生成真正的私有输入数据
        每个银行只知道自己的数据，其他数据对其保密
        """
        party_data = {}
        
        # 银行配置 - 更真实的风险分布
        bank_configs = {
            0: {"name": "Bank Alpha", "risk_bias": 0.1, "avg_credit": 620, "credit_std": 95},   # 高风险银行，低信用评分
            1: {"name": "Bank Beta", "risk_bias": 0.05, "avg_credit": 680, "credit_std": 85},   # 中等风险银行
            2: {"name": "Bank Gamma", "risk_bias": -0.05, "avg_credit": 720, "credit_std": 70}  # 低风险银行，高信用评分
        }
        
        for party_id in range(n_parties):
            np.random.seed(self.seed + party_id * 1000)
            
            config = bank_configs[party_id]
            risk_bias = config["risk_bias"]
            avg_credit = config["avg_credit"]
            credit_std = config["credit_std"]
            
            # 生成客户数据
            customers = []
            for i in range(customers_per_bank):
                # 创建多层次信用评分分布
                if np.random.random() < 0.15:
                    # 15%高风险客户：信用评分300-600
                    credit_score = np.random.uniform(300, 600)
                elif np.random.random() < 0.25:
                    # 25%中低风险客户：信用评分600-700
                    credit_score = np.random.uniform(600, 700)
                elif np.random.random() < 0.35:
                    # 35%中等风险客户：信用评分700-750
                    credit_score = np.random.uniform(700, 750)
                else:
                    # 25%低风险客户：信用评分750-850
                    credit_score = np.random.uniform(750, 850)
                
                # 加入银行特色偏差
                credit_score = np.clip(credit_score + np.random.normal(0, credit_std * 0.2), 300, 850)
                
                # 修正收入范围：生成30K-200K美元的合理范围，适配sfix精度
                income_base = 50 + party_id * 20  # 银行差异：50K, 70K, 90K基础
                income = np.clip(np.random.normal(income_base, 25), 25, 150)  # 25K-150K范围
                
                # 优化债务比率分布，创建更真实的风险分层
                # 使用双峰分布：60%客户低风险，40%客户中高风险
                if np.random.random() < 0.6:
                    # 低风险客户：债务比率20%-45%
                    debt_ratio = np.random.beta(2, 4) * 0.45 + 0.20
                else:
                    # 中高风险客户：债务比率45%-80%
                    debt_ratio = np.random.beta(1.5, 2) * 0.35 + 0.45
                
                debt_ratio = min(0.8, max(0.15, debt_ratio))  # 确保在合理范围内
                
                # 重新计算违约风险 - 更真实的风险分布
                credit_risk = (850 - credit_score) / 550  # 0-1标准化
                income_risk = max(0, (60 - income) / 35)  # 收入越低风险越高
                debt_risk = debt_ratio  # 债务比率直接作为风险
                
                # 综合风险评分
                risk_score = (credit_risk * 0.4 + income_risk * 0.3 + debt_risk * 0.3) + risk_bias
                default_risk = max(0.05, min(0.95, risk_score))  # 更宽的风险范围
                
                customer = {
                    'customer_id': f"BANK{party_id}_CUST_{i:05d}",
                    'credit_score': float(credit_score),
                    'income': float(income),
                    'debt_ratio': float(debt_ratio),
                    'default_risk': float(default_risk)
                }
                customers.append(customer)
            
            party_data[party_id] = {
                'bank_name': config["name"],
                'customer_count': customers_per_bank,
                'financial_data': customers  # Use 'financial_data' key for consistency
            }
            
            logger.info(f"Generated {customers_per_bank} customers for {config['name']}")
        
        return party_data
    
    def generate_medical_mpc_data(self, n_parties: int = 3, patients_per_hospital: int = 50) -> Dict[int, Dict]:
        """
        为医疗MPC生成增强的私有输入数据
        支持medical_joint_analysis.mpc程序的数据格式
        每个医院只知道自己的患者数据，其他数据对其保密
        """
        party_data = {}
        
        # 增强的医院配置 - 基于专科特点
        hospital_configs = {
            0: {
                "name": "综合医院(心脏科)", 
                "specialization": "cardiology",
                "avg_age": 65, 
                "age_std": 12,
                "baseline_range": (40, 55),  # 心脏病患者基线较低
                "treatment_effectiveness": 0.65,
                "adverse_risk": 0.15
            },
            1: {
                "name": "研究医学中心(肿瘤科)", 
                "specialization": "oncology",
                "avg_age": 58, 
                "age_std": 15,
                "baseline_range": (35, 50),  # 肿瘤患者基线最低
                "treatment_effectiveness": 0.60,
                "adverse_risk": 0.25
            },
            2: {
                "name": "大学医院(神经科)", 
                "specialization": "neurology",
                "avg_age": 62, 
                "age_std": 18,
                "baseline_range": (45, 60),  # 神经科基线中等
                "treatment_effectiveness": 0.70,
                "adverse_risk": 0.10
            }
        }
        
        for party_id in range(n_parties):
            np.random.seed(self.seed + party_id * 2000)
            
            config = hospital_configs[party_id]
            
            # 生成患者数据
            patients = []
            for i in range(patients_per_hospital):
                # 1. 患者年龄
                age = np.clip(np.random.normal(config["avg_age"], config["age_std"]), 18, 90)
                
                # 2. 基线健康评分 (0-100分，考虑年龄因素)
                baseline_min, baseline_max = config["baseline_range"]
                baseline_score = np.random.uniform(baseline_min, baseline_max)
                # 年龄越大，基线分数稍微降低
                age_factor = max(0, (age - 40) * 0.15)
                baseline_score = max(0, baseline_score - age_factor)
                
                # 3. 主要疗效指标 (基于基线+治疗效果)
                treatment_improvement = np.random.normal(25, 12)  # 平均改善25分
                if np.random.random() > config["treatment_effectiveness"]:
                    treatment_improvement *= 0.5  # 部分患者治疗效果较差
                
                primary_outcome = min(100, max(0, baseline_score + treatment_improvement))
                
                # 4. 不良反应严重程度 (0-10分)
                if np.random.random() < config["adverse_risk"]:
                    adverse_event = np.random.exponential(3.0)  # 有不良反应时的严重程度
                else:
                    adverse_event = np.random.exponential(1.0)  # 轻微或无不良反应
                
                adverse_event = min(10, max(0, adverse_event))
                
                # 创建患者记录
                patient = {
                    'patient_id': f"HOSP{party_id}_PAT_{i:05d}",
                    'age': int(age),
                    'baseline_score': int(baseline_score),
                    'primary_outcome': int(primary_outcome),
                    'adverse_event': int(adverse_event),
                    'improvement': int(primary_outcome - baseline_score)
                }
                patients.append(patient)
            
            party_data[party_id] = {
                'hospital_name': config["name"],
                'specialization': config["specialization"],
                'patient_count': patients_per_hospital,
                'medical_data': patients
            }
            
            # 计算统计信息
            avg_age = np.mean([p['age'] for p in patients])
            avg_baseline = np.mean([p['baseline_score'] for p in patients])
            avg_outcome = np.mean([p['primary_outcome'] for p in patients])
            avg_improvement = np.mean([p['improvement'] for p in patients])
            effectiveness_rate = np.mean([p['improvement'] >= 20 for p in patients]) * 100
            avg_adverse = np.mean([p['adverse_event'] for p in patients])
            
            logger.info(f"Generated {patients_per_hospital} patients for {config['name']}")
            logger.info(f"  平均年龄: {avg_age:.1f}岁, 基线: {avg_baseline:.1f}分")
            logger.info(f"  疗效: {avg_outcome:.1f}分, 改善: {avg_improvement:.1f}分")
            logger.info(f"  有效率: {effectiveness_rate:.1f}%, 不良反应: {avg_adverse:.1f}分")
        
        return party_data
    
    def save_mpc_input_files(self, party_data: Dict[int, Dict], output_dir: str = "Player-Data"):
        """
        将参与方数据保存为MP-SPDZ输入文件格式
        每个参与方只能访问自己的输入文件
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        saved_files = {}
        
        for party_id, data in party_data.items():
            # 创建该参与方的输入文件
            input_file = output_path / f"Input-P{party_id}-0"
            
            with open(input_file, 'w') as f:
                if 'financial_data' in data:
                    # 金融数据格式
                    f.write(f"{data['customer_count']}\n")
                    for customer in data['financial_data']:
                        f.write(f"{customer['credit_score']:.2f}\n")
                        f.write(f"{customer['income']:.2f}\n") 
                        f.write(f"{customer['debt_ratio']:.6f}\n")
                elif 'medical_data' in data:
                    # 增强医疗数据格式 - 匹配medical_joint_analysis.mpc程序
                    for patient in data['medical_data']:
                        # 按照medical_joint_analysis.mpc的读取顺序写入
                        f.write(f"{patient['age']}\n")              # 患者年龄
                        f.write(f"{patient['baseline_score']}\n")   # 基线健康评分
                        f.write(f"{patient['primary_outcome']}\n")  # 主要疗效指标
                        f.write(f"{patient['adverse_event']}\n")    # 不良反应严重程度
            
            saved_files[party_id] = str(input_file)
            logger.info(f"Saved Party {party_id} input to {input_file}")
        
        return saved_files
    
    def create_mpc_network_config(self, n_parties: int = 3, base_port: int = 5000):
        """创建MP-SPDZ网络配置文件"""
        
        # 创建 hosts 文件
        hosts_content = []
        for i in range(n_parties):
            hosts_content.append(f"localhost:{base_port + i}\n")
        
        with open("hosts", 'w') as f:
            f.writelines(hosts_content)
        
        logger.info(f"Created network config for {n_parties} parties on ports {base_port}-{base_port + n_parties - 1}")
        
        return "hosts"

def generate_certificates_for_mpc(n_parties: int = 3):
    """为MPC参与方生成SSL证书（如果需要）"""
    
    cert_dir = Path("certs_financial")
    cert_dir.mkdir(exist_ok=True)
    
    # 简化版本：创建证书占位符文件
    for party_id in range(n_parties):
        cert_file = cert_dir / f"party_{party_id}.pem"
        key_file = cert_dir / f"party_{party_id}.key"
        
        # 在真实环境中，这里应该生成真正的SSL证书
        with open(cert_file, 'w') as f:
            f.write(f"# Certificate for Party {party_id}\n")
        with open(key_file, 'w') as f:
            f.write(f"# Private key for Party {party_id}\n")
    
    logger.info(f"Generated certificate files for {n_parties} parties")
    return str(cert_dir)

def main_medical_scenario():
    """医疗场景主函数"""
    print("🏥 生成医疗机构联合研究MPC数据...")
    print("=" * 60)
    
    # 生成MPC数据
    generator = MPCDataGenerator()
    
    # 生成医疗数据
    medical_data = generator.generate_medical_mpc_data(n_parties=3, patients_per_hospital=50)
    
    # 保存输入文件
    input_files = generator.save_mpc_input_files(medical_data, output_dir="../Player-Data")
    
    # 创建网络配置
    network_config = generator.create_mpc_network_config()
    
    print("\n📋 医疗MPC数据生成摘要:")
    print("-" * 40)
    print(f"参与医院数: {len(medical_data)}")
    print(f"总患者数: {sum(data['patient_count'] for data in medical_data.values())}")
    
    # 显示各医院详细信息
    for party_id, data in medical_data.items():
        patients = data['medical_data']
        avg_age = np.mean([p['age'] for p in patients])
        avg_improvement = np.mean([p['improvement'] for p in patients])
        effectiveness_rate = np.mean([p['improvement'] >= 20 for p in patients]) * 100
        
        print(f"\n{data['hospital_name']}:")
        print(f"  专科: {data['specialization']}")
        print(f"  患者数: {data['patient_count']}")
        print(f"  平均年龄: {avg_age:.1f}岁")
        print(f"  平均改善: {avg_improvement:.1f}分")
        print(f"  治疗有效率: {effectiveness_rate:.1f}%")
    
    print(f"\n输入文件: {list(input_files.values())}")
    print(f"网络配置: {network_config}")
    
    print("\n✅ 医疗MPC数据准备完成!")
    print("📋 可以运行以下命令执行MPC协议:")
    print("   python3 compile.py medical_joint_analysis")
    print("   ./shamir-party.x -N 3 -p <party_id> medical_joint_analysis")

def main_financial_scenario():
    """金融场景主函数 - 保持原有逻辑不变"""
    print("🏦 Generating Financial MPC Data...")
    
    # 生成MPC数据
    generator = MPCDataGenerator()
    
    financial_data = generator.generate_financial_mpc_data(n_parties=3, customers_per_bank=100)
    
    # 保存输入文件
    input_files = generator.save_mpc_input_files(financial_data)
    
    # 创建网络配置
    network_config = generator.create_mpc_network_config()
    
    # 生成证书
    cert_dir = generate_certificates_for_mpc()
    
    print("\n📋 MPC Data Generation Summary:")
    print(f"Parties: {len(financial_data)}")
    print(f"Total customers: {sum(data['customer_count'] for data in financial_data.values())}")
    print(f"Input files: {list(input_files.values())}")
    print(f"Network config: {network_config}")
    print(f"Certificates: {cert_dir}/")
    print("\n✅ Ready for MP-SPDZ protocol execution!")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "medical":
        main_medical_scenario()
    elif len(sys.argv) > 1 and sys.argv[1] == "financial":
        main_financial_scenario()
    else:
        # 默认行为保持不变 - 运行金融场景
        main_financial_scenario()