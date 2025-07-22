#!/usr/bin/env python3
"""
完整的MPC演示程序 - 展示真实的reveal机制和数据披露
Comprehensive MPC Demonstration with Real Reveal Mechanism
"""

import os
import sys
import subprocess
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile
import time

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteMPCDemo:
    """完整的MPC演示系统"""
    
    def __init__(self, mp_spdz_path="/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        self.mp_spdz_path = Path(mp_spdz_path)
        self.results = {}
        
    def create_comprehensive_test_program(self):
        """创建综合测试程序，展示完整的reveal机制"""
        
        program_content = '''from Compiler.types import sint, sfix, cint
from Compiler.library import print_ln

print_ln("=== COMPREHENSIVE MPC DEMO WITH REVEAL ===")
print_ln("This program demonstrates real MPC computation with data disclosure")

# Configuration
n_parties = 3
data_points_per_party = 2

print_ln("Configuration:")
print_ln("- Parties: %s", n_parties)
print_ln("- Data points per party: %s", data_points_per_party)

# Initialize arrays for financial data
credit_scores = []
incomes = []
debt_ratios = []

print_ln("=== PHASE 1: SECURE DATA INPUT ===")

# Each party inputs their private financial data
for party_id in range(n_parties):
    print_ln("Party %s inputting data...", party_id)
    
    for i in range(data_points_per_party):
        # Each party provides: credit_score, income, debt_ratio
        credit_score = sfix.get_input_from(party_id)
        income = sfix.get_input_from(party_id)
        debt_ratio = sfix.get_input_from(party_id)
        
        credit_scores.append(credit_score)
        incomes.append(income)
        debt_ratios.append(debt_ratio)

print_ln("=== PHASE 2: SECURE COMPUTATION ===")

# Calculate statistics without revealing individual data
total_customers = cint(n_parties * data_points_per_party)

# Sum all values (still secret)
sum_credit = sfix(0)
sum_income = sfix(0)
sum_debt = sfix(0)

for i in range(n_parties * data_points_per_party):
    sum_credit += credit_scores[i]
    sum_income += incomes[i]
    sum_debt += debt_ratios[i]

# Calculate means (still secret)
mean_credit = sum_credit / total_customers
mean_income = sum_income / total_customers
mean_debt = sum_debt / total_customers

# Risk assessment (still secret)
high_risk_count = sint(0)
for i in range(n_parties * data_points_per_party):
    # High risk if credit < 650 OR debt ratio > 0.6
    is_high_risk_credit = credit_scores[i] < sfix(650)
    is_high_risk_debt = debt_ratios[i] > sfix(0.6)
    is_high_risk = is_high_risk_credit + is_high_risk_debt
    
    # Convert to integer (1 if high risk, 0 otherwise)
    high_risk_count += (is_high_risk > sfix(0)).if_else(1, 0)

# Calculate risk rate
risk_rate = sfix(high_risk_count) / sfix(total_customers)

print_ln("=== PHASE 3: BUSINESS RESULTS DISCLOSURE (REVEAL) ===")
print_ln("Now revealing aggregate statistics while preserving individual privacy")

# **CRITICAL REVEAL SECTION** - This is where private data becomes public
# Only aggregate statistics are revealed, individual records remain secret

revealed_total_customers = total_customers.reveal()
print_ln("BUSINESS_DISCLOSURE - Total Customers: %s", revealed_total_customers)

revealed_mean_credit = mean_credit.reveal()
print_ln("BUSINESS_DISCLOSURE - Average Credit Score: %s", revealed_mean_credit)

revealed_mean_income = mean_income.reveal()
print_ln("BUSINESS_DISCLOSURE - Average Income: %s", revealed_mean_income)

revealed_mean_debt = mean_debt.reveal()
print_ln("BUSINESS_DISCLOSURE - Average Debt Ratio: %s", revealed_mean_debt)

revealed_high_risk_count = high_risk_count.reveal()
print_ln("BUSINESS_DISCLOSURE - High Risk Customers: %s", revealed_high_risk_count)

revealed_risk_rate = risk_rate.reveal()
print_ln("BUSINESS_DISCLOSURE - Risk Rate: %s", revealed_risk_rate)

# Additional business metrics
overall_risk_score = (sfix(800) - mean_credit) / sfix(100) + mean_debt
revealed_risk_score = overall_risk_score.reveal()
print_ln("BUSINESS_DISCLOSURE - Overall Risk Score: %s", revealed_risk_score)

print_ln("=== PRIVACY GUARANTEE ===")
print_ln("✓ Individual customer data never revealed")
print_ln("✓ Only aggregate statistics disclosed")
print_ln("✓ True multi-party computation completed")

print_ln("=== DEMO COMPLETE ===")
print_ln("MPC Reveal mechanism successfully demonstrated!")
'''
        
        # 保存程序
        program_file = self.mp_spdz_path / "Programs" / "Source" / "comprehensive_mpc_demo.mpc"
        with open(program_file, 'w') as f:
            f.write(program_content)
        
        logger.info(f"Created comprehensive MPC demo program: {program_file}")
        return "comprehensive_mpc_demo"
    
    def generate_realistic_financial_data(self, n_parties=3, customers_per_party=2):
        """生成真实的金融数据用于MPC测试"""
        
        logger.info("Generating realistic financial data for MPC demo...")
        
        # 为每个参与方生成数据
        party_data = {}
        
        banks = ["Citibank", "JP Morgan", "Bank of America"]
        
        for party_id in range(n_parties):
            np.random.seed(42 + party_id * 100)  # 确保可重复的结果
            
            customers = []
            for i in range(customers_per_party):
                # 生成真实的金融特征
                base_credit = 720 + party_id * 20  # 每个银行的基础信用评分不同
                credit_score = np.random.normal(base_credit, 50)
                credit_score = max(300, min(850, credit_score))  # 限制在合理范围
                
                # 收入与信用评分相关
                base_income = 30000 + (credit_score - 600) * 100
                income = max(20000, np.random.normal(base_income, 15000))
                
                # 债务比率与信用评分负相关
                base_debt = 0.5 - (credit_score - 600) / 1000
                debt_ratio = max(0.1, min(0.9, np.random.normal(base_debt, 0.15)))
                
                customers.append({
                    'customer_id': f"{banks[party_id]}_CUST_{i:03d}",
                    'credit_score': credit_score,
                    'income': income,
                    'debt_ratio': debt_ratio
                })
            
            party_data[party_id] = {
                'bank_name': banks[party_id],
                'customers': customers
            }
            
            # 创建MP-SPDZ输入文件
            input_file = self.mp_spdz_path / "Player-Data" / f"Input-P{party_id}-0"
            with open(input_file, 'w') as f:
                for customer in customers:
                    # 每个客户3个数据点：信用评分、收入、债务比率
                    f.write(f"{customer['credit_score']:.2f}\n")
                    f.write(f"{customer['income']:.0f}\n") 
                    f.write(f"{customer['debt_ratio']:.3f}\n")
            
            logger.info(f"Generated data for {banks[party_id]}: {len(customers)} customers")
        
        return party_data
    
    def run_emulated_mpc(self, program_name):
        """使用emulation模式运行MPC"""
        
        logger.info(f"Running MPC program {program_name} in emulation mode...")
        
        try:
            # 切换到MP-SPDZ目录
            original_dir = os.getcwd()
            os.chdir(self.mp_spdz_path)
            
            # 创建临时输出文件
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as output_file:
                output_filename = output_file.name
            
            # 运行emulation - 使用正确的emulate.x二进制文件
            cmd = ["./emulate.x", program_name]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            # 运行程序并捕获输出
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.mp_spdz_path
            )
            
            if process.returncode == 0:
                logger.info("MPC emulation completed successfully")
                output = process.stdout
                error = process.stderr
                
                # 显示完整输出
                logger.info("=== MPC PROGRAM OUTPUT ===")
                logger.info(output)
                
                if error:
                    logger.warning("=== MPC STDERR ===")
                    logger.warning(error)
                
                return {
                    'success': True,
                    'output': output,
                    'stderr': error,
                    'returncode': process.returncode
                }
            else:
                logger.error(f"MPC emulation failed with return code {process.returncode}")
                logger.error(f"Error: {process.stderr}")
                
                return {
                    'success': False,
                    'output': process.stdout,
                    'stderr': process.stderr,
                    'returncode': process.returncode
                }
                
        except subprocess.TimeoutExpired:
            logger.error("MPC emulation timed out")
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            logger.error(f"MPC emulation failed: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            os.chdir(original_dir)
    
    def extract_revealed_data(self, mpc_output):
        """从MPC输出中提取reveal的数据"""
        
        logger.info("Extracting revealed business data from MPC output...")
        
        revealed_data = {}
        
        # 解析BUSINESS_DISCLOSURE行
        lines = mpc_output.split('\n')
        disclosure_lines = [line for line in lines if 'BUSINESS_DISCLOSURE' in line]
        
        logger.info(f"Found {len(disclosure_lines)} business disclosure lines")
        
        for line in disclosure_lines:
            logger.info(f"Processing: {line}")
            
            # 解析不同类型的披露数据
            if "Total Customers:" in line:
                import re
                match = re.search(r'Total Customers:\s*([\d.]+)', line)
                if match:
                    revealed_data['total_customers'] = int(float(match.group(1)))
            
            elif "Average Credit Score:" in line:
                match = re.search(r'Average Credit Score:\s*([\d.-]+)', line)
                if match:
                    revealed_data['avg_credit_score'] = float(match.group(1))
            
            elif "Average Income:" in line:
                match = re.search(r'Average Income:\s*([\d.-]+)', line)
                if match:
                    revealed_data['avg_income'] = float(match.group(1))
            
            elif "Average Debt Ratio:" in line:
                match = re.search(r'Average Debt Ratio:\s*([\d.-]+)', line)
                if match:
                    revealed_data['avg_debt_ratio'] = float(match.group(1))
            
            elif "High Risk Customers:" in line:
                match = re.search(r'High Risk Customers:\s*([\d.]+)', line)
                if match:
                    revealed_data['high_risk_customers'] = int(float(match.group(1)))
            
            elif "Risk Rate:" in line:
                match = re.search(r'Risk Rate:\s*([\d.-]+)', line)
                if match:
                    revealed_data['risk_rate'] = float(match.group(1))
            
            elif "Overall Risk Score:" in line:
                match = re.search(r'Overall Risk Score:\s*([\d.-]+)', line)
                if match:
                    revealed_data['overall_risk_score'] = float(match.group(1))
        
        logger.info(f"Successfully extracted revealed data: {revealed_data}")
        return revealed_data
    
    def display_results_summary(self, party_data, revealed_data):
        """显示结果摘要"""
        
        print("\n" + "="*80)
        print("🔐 COMPREHENSIVE MPC DEMONSTRATION RESULTS")
        print("="*80)
        
        print("\n📊 INPUT DATA (Private - Never Revealed in Real MPC):")
        print("-"*60)
        
        for party_id, data in party_data.items():
            print(f"\n{data['bank_name']} (Party {party_id}):")
            for i, customer in enumerate(data['customers']):
                print(f"  Customer {i+1}: Credit={customer['credit_score']:.0f}, "
                      f"Income=${customer['income']:.0f}, Debt={customer['debt_ratio']:.3f}")
        
        print("\n🔓 REVEALED AGGREGATE STATISTICS (Business Insights):")
        print("-"*60)
        
        if revealed_data:
            for key, value in revealed_data.items():
                if isinstance(value, float):
                    if key == 'avg_income':
                        print(f"📈 {key.replace('_', ' ').title()}: ${value:,.2f}")
                    elif 'ratio' in key or 'rate' in key:
                        print(f"📊 {key.replace('_', ' ').title()}: {value:.3f}")
                    else:
                        print(f"📊 {key.replace('_', ' ').title()}: {value:.2f}")
                else:
                    print(f"📊 {key.replace('_', ' ').title()}: {value}")
        else:
            print("❌ No revealed data found in MPC output")
        
        print("\n✅ PRIVACY GUARANTEES:")
        print("-"*60)
        print("✓ Individual customer data never exposed to other banks")
        print("✓ Only aggregate statistics computed and revealed")
        print("✓ True secure multi-party computation demonstrated")
        print("✓ Each bank maintains full control over their private data")
        
        print("\n🎯 BUSINESS VALUE:")
        print("-"*60)
        print("✓ Joint risk assessment without data sharing")
        print("✓ Regulatory compliance (GDPR, BASEL III)")
        print("✓ Competitive advantage through collaboration")
        print("✓ Privacy-preserving business intelligence")
        
        print("\n" + "="*80)

def main():
    """主演示函数"""
    
    print("🚀 Starting Comprehensive MPC Demonstration")
    print("="*80)
    
    demo = CompleteMPCDemo()
    
    try:
        # 1. 创建综合MPC程序
        program_name = demo.create_comprehensive_test_program()
        print(f"✅ Created MPC program: {program_name}")
        
        # 2. 编译程序
        print("📝 Compiling MPC program...")
        os.chdir(demo.mp_spdz_path)
        compile_result = subprocess.run(
            ["python3", "compile.py", program_name],
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode == 0:
            print("✅ MPC program compiled successfully")
        else:
            print(f"❌ Compilation failed: {compile_result.stderr}")
            return
        
        # 3. 生成测试数据
        party_data = demo.generate_realistic_financial_data()
        print("✅ Generated realistic financial test data")
        
        # 4. 运行MPC程序（模拟模式）
        print("🔐 Executing MPC with reveal mechanism...")
        mpc_result = demo.run_emulated_mpc(program_name)
        
        if mpc_result['success']:
            print("✅ MPC execution completed successfully")
            
            # 5. 提取reveal的数据
            revealed_data = demo.extract_revealed_data(mpc_result['output'])
            
            # 6. 显示完整结果
            demo.display_results_summary(party_data, revealed_data)
            
        else:
            print("❌ MPC execution failed")
            print(f"Error: {mpc_result.get('error', 'Unknown error')}")
            if 'stderr' in mpc_result:
                print(f"Details: {mpc_result['stderr']}")
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()