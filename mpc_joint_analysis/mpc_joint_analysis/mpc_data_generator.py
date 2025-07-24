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
        
        # 银行配置
        bank_configs = {
            0: {"name": "Bank Alpha", "risk_bias": -0.1, "avg_credit": 720},
            1: {"name": "Bank Beta", "risk_bias": 0.0, "avg_credit": 730},
            2: {"name": "Bank Gamma", "risk_bias": 0.1, "avg_credit": 740}
        }
        
        for party_id in range(n_parties):
            np.random.seed(self.seed + party_id * 1000)
            
            config = bank_configs[party_id]
            risk_bias = config["risk_bias"]
            avg_credit = config["avg_credit"]
            
            # 生成客户数据
            customers = []
            for i in range(customers_per_bank):
                # 生成客户基础数据
                credit_score = np.clip(np.random.normal(avg_credit, 80), 300, 850)
                income = np.random.lognormal(10.5 + party_id * 0.1, 0.8)
                debt_ratio = np.random.beta(2, 5) * 0.8
                
                # 计算违约风险 (基于信用评分和债务比率)
                risk_score = (850 - credit_score) / 550 * 0.5 + debt_ratio * 0.4 + risk_bias
                default_risk = max(0.01, min(0.99, risk_score))
                
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
    
    def generate_medical_mpc_data(self, n_parties: int = 3, patients_per_hospital: int = 100) -> Dict[int, Dict]:
        """
        为医疗MPC生成真正的私有输入数据
        每个医院只知道自己的患者数据，其他数据对其保密
        """
        party_data = {}
        
        # 医院配置
        hospital_configs = {
            0: {"name": "General Hospital", "treatment_bias": 0.1, "avg_age": 55},
            1: {"name": "Specialty Center", "treatment_bias": 0.2, "avg_age": 60},
            2: {"name": "Research Hospital", "treatment_bias": 0.15, "avg_age": 58}
        }
        
        for party_id in range(n_parties):
            np.random.seed(self.seed + party_id * 2000)
            
            config = hospital_configs[party_id]
            treatment_bias = config["treatment_bias"]
            avg_age = config["avg_age"]
            
            # 生成患者数据
            patients = []
            for i in range(patients_per_hospital):
                # 生成患者基础数据
                age = np.clip(np.random.normal(avg_age, 15), 18, 90)
                baseline_score = np.random.normal(50, 15)
                treatment_success = np.random.binomial(1, 0.6 + treatment_bias)
                
                # 添加医疗数据特有的字段
                patient = {
                    'patient_id': f"HOSP{party_id}_PAT_{i:05d}",
                    'age': float(age),
                    'baseline_score': float(baseline_score),
                    'treatment_success': float(treatment_success)
                }
                patients.append(patient)
            
            party_data[party_id] = {
                'hospital_name': config["name"],
                'patient_count': patients_per_hospital,
                'medical_data': patients  # Use 'medical_data' key for consistency
            }
            
            logger.info(f"Generated {patients_per_hospital} patients for {config['name']}")
        
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
                    # 医疗数据格式
                    f.write(f"{data['patient_count']}\n")
                    for patient in data['medical_data']:
                        f.write(f"{patient['age']:.2f}\n")
                        f.write(f"{patient['baseline_score']:.2f}\n")
                        f.write(f"{patient['treatment_success']:.0f}\n")
            
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

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 生成MPC数据
    generator = MPCDataGenerator()
    
    print("🏦 Generating Financial MPC Data...")
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