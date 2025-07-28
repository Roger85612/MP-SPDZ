#!/usr/bin/env python3
"""
测试增强金融MPC程序的简化执行脚本
使用Shamir协议快速验证financial_joint_analysis.mpc
"""

import os
import sys
import subprocess
import threading
import queue
import time
import re
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleFinancialMPCTest:
    """简化的金融MPC测试器"""
    
    def __init__(self, mp_spdz_path="/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        self.mp_spdz_path = Path(mp_spdz_path)
        self.program_name = "financial_joint_analysis"
        self.n_parties = 3
        
    def test_enhanced_financial_mpc(self):
        """测试增强的金融MPC程序"""
        
        print("🏦 测试增强金融MPC程序 - financial_joint_analysis.mpc")
        print("=" * 80)
        
        try:
            # 编译程序
            print("\n🔧 编译MPC程序...")
            if not self._compile_program():
                print("❌ 编译失败")
                return False
            
            # 执行Shamir协议
            print("\n🔐 执行Shamir协议...")
            results = self._execute_shamir_simple()
            
            if results.get('success', False):
                print("✅ 协议执行成功")
                print("\n📊 金融风险评估结果:")
                print("-" * 60)
                self._display_results(results)
                return True
            else:
                print(f"❌ 协议执行失败: {results.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"测试失败: {e}")
            print(f"❌ 测试失败: {e}")
            return False
    
    def _compile_program(self):
        """编译MPC程序"""
        try:
            os.chdir(self.mp_spdz_path)
            result = subprocess.run(
                ["python3", "compile.py", self.program_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"   ✅ {self.program_name}.mpc 编译成功")
                return True
            else:
                print(f"   ❌ 编译失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ 编译异常: {e}")
            return False
    
    def _execute_shamir_simple(self):
        """执行简化Shamir协议"""
        try:
            os.chdir(self.mp_spdz_path)
            
            # 创建输出队列
            output_queues = [queue.Queue() for _ in range(self.n_parties)]
            threads = []
            
            # 启动所有参与方线程
            for party_id in range(self.n_parties):
                thread = threading.Thread(
                    target=self._run_party_thread,
                    args=(party_id, output_queues[party_id])
                )
                threads.append(thread)
                thread.start()
                time.sleep(0.5)  # 避免竞争启动
            
            # 等待完成并收集结果
            results = {}
            for i, thread in enumerate(threads):
                thread.join(timeout=30)  # 30秒超时
                
                try:
                    result = output_queues[i].get_nowait()
                    results[i] = result
                except queue.Empty:
                    results[i] = {
                        'party_id': i,
                        'return_code': -1,
                        'output': '超时或无输出'
                    }
            
            # 检查成功结果
            successful_parties = [r for r in results.values() if r.get('return_code') == 0]
            
            if successful_parties:
                logger.info(f"Shamir协议执行成功: {len(successful_parties)}/{self.n_parties} 参与方成功")
                return self._parse_financial_output(successful_parties[0]['output'])
            else:
                logger.error("Shamir协议执行失败: 所有参与方都失败")
                return {'success': False, 'error': 'All parties failed'}
                
        except Exception as e:
            logger.error(f"Shamir协议执行异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_party_thread(self, party_id, output_queue):
        """运行单个参与方线程"""
        try:
            cmd = [
                "./shamir-party.x", 
                "-N", str(self.n_parties), 
                "-p", str(party_id), 
                "--batch-size", "8192",
                self.program_name
            ]
            
            logger.info(f"启动参与方{party_id}: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.mp_spdz_path
            )
            
            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                output_lines.append(line.strip())
            
            return_code = process.wait()
            stderr_output = process.stderr.read()
            
            result = {
                'party_id': party_id,
                'return_code': return_code,
                'output': '\n'.join(output_lines),
                'stderr': stderr_output
            }
            
            output_queue.put(result)
            logger.info(f"参与方{party_id}完成, 返回码: {return_code}")
            
        except Exception as e:
            logger.error(f"参与方{party_id}执行失败: {e}")
            output_queue.put({
                'party_id': party_id,
                'return_code': -1,
                'output': f'执行异常: {str(e)}',
                'stderr': str(e)
            })
    
    def _parse_financial_output(self, output):
        """解析金融MPC输出"""
        try:
            results = {'success': True}
            
            # 查找FINANCIAL_DISCLOSURE结果
            disclosure_lines = [line for line in output.split('\n') if 'FINANCIAL_DISCLOSURE' in line]
            
            for line in disclosure_lines:
                # 解析金融统计结果
                if "平均信用评分:" in line:
                    match = re.search(r"平均信用评分:\s*([0-9.-]+)", line)
                    if match:
                        results['mean_credit_score'] = float(match.group(1))
                elif "平均年收入:" in line:
                    match = re.search(r"平均年收入:\s*([0-9.-]+)", line)
                    if match:
                        results['mean_income'] = float(match.group(1))
                elif "平均债务收入比:" in line:
                    match = re.search(r"平均债务收入比:\s*([0-9.-]+)", line)
                    if match:
                        results['mean_debt_ratio'] = float(match.group(1))
                elif "总体违约率:" in line:
                    match = re.search(r"总体违约率:\s*([0-9.-]+)", line)
                    if match:
                        results['default_rate'] = float(match.group(1))
                elif "优秀信用客户数:" in line:
                    match = re.search(r"优秀信用客户数:\s*([0-9.-]+)", line)
                    if match:
                        results['excellent_customers'] = int(float(match.group(1)))
                elif "良好信用客户数:" in line:
                    match = re.search(r"良好信用客户数:\s*([0-9.-]+)", line)
                    if match:
                        results['good_customers'] = int(float(match.group(1)))
                elif "高风险客户比例:" in line:
                    match = re.search(r"高风险客户比例:\s*([0-9.-]+)", line)
                    if match:
                        results['high_risk_rate'] = float(match.group(1))
                elif "优质客户比例:" in line:
                    match = re.search(r"优质客户比例:\s*([0-9.-]+)", line)
                    if match:
                        results['premium_rate'] = float(match.group(1))
            
            logger.info(f"解析到 {len(results)-1} 个金融统计结果")
            
            # 调试输出
            logger.info(f"找到的FINANCIAL_DISCLOSURE行数: {len(disclosure_lines)}")
            for i, line in enumerate(disclosure_lines[:5]):
                logger.info(f"披露行{i}: {line}")
            
            return results
            
        except Exception as e:
            logger.error(f"输出解析失败: {e}")
            return {'success': False, 'error': f'Parse error: {e}'}
    
    def _display_results(self, results):
        """显示金融结果"""
        if 'mean_credit_score' in results:
            print(f"📊 平均信用评分: {results['mean_credit_score']:.1f}")
        if 'mean_income' in results:
            print(f"💰 平均年收入: ${results['mean_income']:,.0f}")
        if 'mean_debt_ratio' in results:
            print(f"📈 平均债务收入比: {results['mean_debt_ratio']:.1f}%")
        if 'default_rate' in results:
            print(f"⚠️ 总体违约率: {results['default_rate']:.2f}%")
        if 'excellent_customers' in results:
            print(f"⭐ 优秀信用客户: {results['excellent_customers']}人")
        if 'good_customers' in results:
            print(f"✅ 良好信用客户: {results['good_customers']}人")
        if 'high_risk_rate' in results:
            print(f"🚨 高风险客户比例: {results['high_risk_rate']:.1f}%")
        if 'premium_rate' in results:
            print(f"💎 优质客户比例: {results['premium_rate']:.1f}%")
        
        # 业务解释
        if 'default_rate' in results:
            rate = results['default_rate']
            if rate <= 2:
                print("   ✅ 违约率优秀")
            elif rate <= 5:
                print("   ⚠️ 违约率可接受")
            else:
                print("   🚨 违约风险较高")

def main():
    """主函数"""
    tester = SimpleFinancialMPCTest()
    success = tester.test_enhanced_financial_mpc()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 增强金融MPC程序测试成功!")
    else:
        print("❌ 增强金融MPC程序测试失败!")
    print("=" * 80)

if __name__ == "__main__":
    main()