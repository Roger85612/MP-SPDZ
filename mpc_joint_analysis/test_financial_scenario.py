#!/usr/bin/env python3
"""
金融场景MPC测试程序
专门用于调试金融场景中Y值为NaN的问题
"""

import os
import sys
import subprocess
import threading
import time
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
import signal
import queue
import select

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialMPCTester:
    """金融场景MPC测试器"""
    
    def __init__(self, mp_spdz_path="/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        self.mp_spdz_path = Path(mp_spdz_path)
        self.processes = []
        
    def generate_financial_data(self, n_parties=3, data_size=10):
        """生成金融场景的输入数据"""
        logger.info(f"生成金融数据: {n_parties}方, 每方{data_size}数据点")
        
        np.random.seed(42)
        banks = ["Citibank", "JP Morgan", "Bank of America"]
        
        for party_id in range(n_parties):
            base_credit = 720 + party_id * 15
            base_income = 4500 + party_id * 1000
                        
            # 生成数据
            credit_scores = np.random.normal(base_credit, 60, data_size)
            credit_scores = np.clip(credit_scores, 300, 850)
            incomes = np.random.normal(base_income, 15000, data_size)
            incomes = np.clip(incomes, 2000, 15000)
            
            # 创建输入文件
            input_file = self.mp_spdz_path / f"Player-Data/Input-P{party_id}-0" 
            with open(input_file, 'w') as f:
                # 写入X变量（信用评分）
                for score in credit_scores:
                    f.write(f"{int(score)}\n")
                # 写入Y变量（收入，预先缩放为百美元以避免sfix精度问题）
                for income in incomes:
                    scaled_income = int(income // 100)  # 缩放为百美元
                    f.write(f"{scaled_income}\n")
            
            logger.info(f"Generated data for {banks[party_id]}:")
            logger.info(f"  - Credit scores: {credit_scores[:5]} (showing first 5)")
            logger.info(f"  - Average credit: {np.mean(credit_scores):.1f}")
            logger.info(f"  - Incomes: {incomes[:5]} (showing first 5)")
            logger.info(f"  - Average income: {np.mean(incomes):.0f}")
            logger.info(f"  - Scaled incomes: {[int(x//100) for x in incomes[:5]]} (showing first 5)")
    
    def compile_program(self, program_name):
        """编译MPC程序"""
        logger.info(f"编译MPC程序: {program_name}")
        
        try:
            os.chdir(self.mp_spdz_path)
            result = subprocess.run(
                ["python3", "compile.py", program_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"程序编译成功: {program_name}")
                return True
            else:
                logger.error(f"程序编译失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"编译异常: {e}")
            return False
    
    def run_party_process(self, protocol, party_id, n_parties, program_name, output_queue):
        """运行单个参与方的进程"""
        logger.info(f"启动{protocol}协议 - 参与方{party_id}")
        
        try:
            os.chdir(self.mp_spdz_path)
            
            # 根据协议选择可执行文件
            if protocol == "mascot":
                executable = "./mascot-party.x"
            elif protocol == "shamir":
                executable = "./shamir-party.x"
            else:
                raise ValueError(f"不支持的协议: {protocol}")
            
            # 启动进程
            cmd = [executable, "-N", str(n_parties), "-p", str(party_id), "--batch-size", "8192", program_name]
            logger.info(f"运行命令: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(process)
            
            # 读取输出
            output_lines = []
            while True:
                # 使用select检查是否有输出可读
                ready, _, _ = select.select([process.stdout, process.stderr], [], [], 1.0)
                
                if process.stdout in ready:
                    line = process.stdout.readline()
                    if line:
                        output_lines.append(f"P{party_id}_STDOUT: {line.strip()}")
                        logger.info(f"P{party_id}: {line.strip()}")
                
                if process.stderr in ready:
                    line = process.stderr.readline()
                    if line:
                        output_lines.append(f"P{party_id}_STDERR: {line.strip()}")
                        logger.warning(f"P{party_id}_ERR: {line.strip()}")
                
                # 检查进程是否结束
                if process.poll() is not None:
                    # 读取剩余输出
                    remaining_stdout, remaining_stderr = process.communicate()
                    if remaining_stdout:
                        for line in remaining_stdout.split('\n'):
                            if line.strip():
                                output_lines.append(f"P{party_id}_STDOUT: {line.strip()}")
                                logger.info(f"P{party_id}: {line.strip()}")
                    if remaining_stderr:
                        for line in remaining_stderr.split('\n'):
                            if line.strip():
                                output_lines.append(f"P{party_id}_STDERR: {line.strip()}")
                                logger.warning(f"P{party_id}_ERR: {line.strip()}")
                    break
            
            output_queue.put({
                'party_id': party_id,
                'return_code': process.returncode,
                'output': '\n'.join(output_lines)
            })
            
            logger.info(f"参与方{party_id}执行完成，返回码: {process.returncode}")
            
        except Exception as e:
            logger.error(f"参与方{party_id}执行异常: {e}")
            output_queue.put({
                'party_id': party_id,
                'return_code': -1,
                'output': f"执行异常: {str(e)}"
            })
    
    def run_mpc_protocol(self, protocol, program_name, n_parties=3, timeout_seconds=60):
        """运行完整的MPC协议"""
        logger.info(f"开始运行{protocol}协议: {program_name}")
        
        # 清理之前的进程
        self.cleanup_processes()
        
        # 创建输出队列
        output_queues = [queue.Queue() for _ in range(n_parties)]
        
        # 启动所有参与方的线程
        threads = []
        for party_id in range(n_parties):
            thread = threading.Thread(
                target=self.run_party_process,
                args=(protocol, party_id, n_parties, program_name, output_queues[party_id])
            )
            threads.append(thread)
            thread.start()
            # 稍微延迟启动，避免竞争
            time.sleep(0.5)
        
        # 等待所有线程完成或超时
        start_time = time.time()
        results = {}
        
        for i, thread in enumerate(threads):
            remaining_time = timeout_seconds - (time.time() - start_time)
            if remaining_time > 0:
                thread.join(timeout=remaining_time)
                
                # 获取输出
                try:
                    result = output_queues[i].get_nowait()
                    results[i] = result
                except queue.Empty:
                    results[i] = {
                        'party_id': i,
                        'return_code': -1,
                        'output': '超时或无输出'
                    }
            else:
                logger.warning(f"参与方{i}执行超时")
                results[i] = {
                    'party_id': i,
                    'return_code': -1,
                    'output': '执行超时'
                }
        
        # 清理进程
        self.cleanup_processes()
        
        return results
    
    def cleanup_processes(self):
        """清理所有子进程"""
        for process in self.processes:
            if process.poll() is None:  # 进程仍在运行
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                except Exception as e:
                    logger.warning(f"清理进程时出错: {e}")
        
        self.processes.clear()
    
    def extract_results(self, results):
        """从MPC输出中提取计算结果"""
        logger.info("提取MPC计算结果")
        
        # 合并所有参与方的输出
        all_output = ""
        for party_id, result in results.items():
            all_output += result['output'] + "\n"
        
        # 打印完整输出用于调试
        print("\n" + "="*80)
        print("完整MPC输出（用于调试）:")
        print("="*80)
        print(all_output)
        print("="*80)
        
        # 提取reveal的数值
        extracted_results = {}
        lines = all_output.split('\n')
        
        for line in lines:
            if 'Mean Y (USD)' in line or 'reveal Mean Y' in line or 'BUSINESS_DISCLOSURE Mean Y' in line:
                # 查找Y均值
                import re
                match = re.search(r'Mean Y.*?:?\s*([\d.-]+|NaN)', line, re.IGNORECASE)
                if match:
                    value_str = match.group(1)
                    if value_str.lower() != 'nan':
                        try:
                            extracted_results['mean_y'] = float(value_str)
                            logger.info(f"提取到 Mean Y: {extracted_results['mean_y']}")
                        except ValueError:
                            logger.warning(f"无法解析Y均值: {value_str}")
                    else:
                        logger.error("检测到Y均值为NaN!")
                        extracted_results['mean_y'] = 'NaN'
        
        return {
            'extracted_results': extracted_results,
            'raw_output': all_output,
            'individual_results': results
        }
    
    def display_results(self, mpc_results):
        """显示结果"""
        print("\n" + "="*80)
        print("🏦 金融场景MPC测试结果")
        print("="*80)
        
        # 显示MPC计算结果
        extracted = mpc_results.get('extracted_results', {})
        if extracted:
            print(f"\n🔓 MPC计算结果:")
            print("-"*60)
            
            for key, value in extracted.items():
                if key == 'mean_y':
                    if value == 'NaN':
                        print(f"❌ 平均年收入: {value} (发现问题!)")
                    else:
                        print(f"✅ 平均年收入: {value} USD")
        else:
            print(f"\n❌ 未能提取到MPC计算结果")
        
        # 显示执行状态
        print(f"\n📊 各参与方执行状态:")
        print("-"*60)
        individual_results = mpc_results.get('individual_results', {})
        for party_id, result in individual_results.items():
            status = "✅ 成功" if result['return_code'] == 0 else "❌ 失败"
            print(f"参与方 {party_id}: {status} (返回码: {result['return_code']})")

def main():
    """主函数 - 专门测试金融场景"""
    print("🚀 启动金融场景MPC测试")
    print("="*80)
    
    tester = FinancialMPCTester()
    
    # 首先编译simple_joint_statistics程序
    if not tester.compile_program("simple_joint_statistics"):
        print("❌ 程序编译失败，退出")
        return
    
    print("\n🏦 测试金融机构联合风险评估 (MASCOT协议)")
    print("-"*60)
    
    try:
        # 生成金融数据
        tester.generate_financial_data(n_parties=3, data_size=10)
        
        # 运行MASCOT协议
        results = tester.run_mpc_protocol("mascot", "simple_joint_statistics", n_parties=3, timeout_seconds=120)
        
        # 提取并显示结果
        mpc_results = tester.extract_results(results)
        tester.display_results(mpc_results)
        
    except Exception as e:
        print(f"❌ 金融场景执行失败: {e}")
        logger.exception("金融场景异常")
    
    # 清理
    tester.cleanup_processes()
    
    print("\n" + "="*80)
    print("🎉 金融场景MPC测试完成!")
    print("="*80)

if __name__ == "__main__":
    # 注册信号处理器以便清理
    def signal_handler(sig, frame):
        print("\n🛑 接收到中断信号，正在清理...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main()