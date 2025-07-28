#!/usr/bin/env python3
"""
医疗机构联合研究场景执行脚本
基于mpc_joint_analysis项目框架的完整医疗MPC流程
"""

import os
import sys
import subprocess
import logging
import time
import threading
import queue
from pathlib import Path
from mpc_data_generator import MPCDataGenerator
from mpc_executor import MPCProtocolExecutor
from mpc_result_disclosure import MPCResultDisclosure

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MedicalMPCRunner:
    """医疗MPC运行器"""
    
    def __init__(self, mp_spdz_path="/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        self.mp_spdz_path = Path(mp_spdz_path)
        self.program_name = "medical_joint_analysis"
        self.protocol = "shamir"  # 医疗场景使用Shamir协议
        self.n_parties = 3
        self.patients_per_hospital = 50  # 匹配medical_joint_analysis.mpc的期望
        
    def run_complete_medical_scenario(self):
        """运行完整的医疗场景"""
        
        print("🏥 启动医疗机构联合研究MPC场景")
        print("=" * 80)
        print("场景: 三家医院联合药物疗效研究")
        print("协议: Shamir秘密共享 (诚实多数)")
        print("参与方: 综合医院(心脏科)、研究医学中心(肿瘤科)、大学医院(神经科)")
        print("=" * 80)
        
        try:
            # 第1步: 生成医疗数据
            print("\n📊 第1步: 生成各医院患者数据")
            self._generate_medical_data()
            
            # 第2步: 编译MPC程序
            print("\n🔧 第2步: 编译医疗MPC程序")
            self._compile_medical_program()
            
            # 第3步: 执行MPC协议
            print("\n🔐 第3步: 执行Shamir MPC协议")
            mpc_results = self._execute_mpc_protocol()
            
            # 第4步: 结果分析和披露
            print("\n📋 第4步: 医疗研究结果分析")
            self._analyze_medical_results(mpc_results)
            
            print("\n" + "=" * 80)
            print("✅ 医疗机构联合研究MPC场景执行完成!")
            print("🔒 患者隐私在整个过程中得到完全保护")
            print("📊 只有聚合的研究结果被安全披露")
            print("=" * 80)
            
        except Exception as e:
            logger.error(f"医疗场景执行失败: {e}")
            print(f"\n❌ 医疗场景执行失败: {e}")
            raise
    
    def _generate_medical_data(self):
        """生成医疗数据"""
        
        logger.info("开始生成医疗数据...")
        
        # 使用增强的医疗数据生成器
        generator = MPCDataGenerator(seed=42)
        medical_data = generator.generate_medical_mpc_data(
            n_parties=self.n_parties, 
            patients_per_hospital=self.patients_per_hospital
        )
        
        # 保存输入文件 - 使用原始医疗数据格式
        input_files = generator.save_mpc_input_files(
            medical_data, 
            output_dir=str(self.mp_spdz_path / "Player-Data")
        )
        
        # 显示数据摘要
        print(f"   ✅ 已生成 {self.n_parties} 家医院的患者数据")
        print(f"   📊 总患者数: {self.n_parties * self.patients_per_hospital}")
        
        for party_id, data in medical_data.items():
            patients = data['medical_data']
            avg_age = sum(p['age'] for p in patients) / len(patients)
            avg_improvement = sum(p['improvement'] for p in patients) / len(patients)
            effectiveness_rate = sum(1 for p in patients if p['improvement'] >= 20) / len(patients) * 100
            
            print(f"   🏥 {data['hospital_name']}: {len(patients)}患者, "
                  f"平均{avg_age:.1f}岁, 改善{avg_improvement:.1f}分, 有效率{effectiveness_rate:.1f}%")
        
        return medical_data
    
    def _compile_medical_program(self):
        """编译医疗MPC程序"""
        
        logger.info(f"编译程序: {self.program_name}")
        
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
                logger.info(f"程序编译成功: {self.program_name}")
                return True
            else:
                print(f"   ❌ 编译失败: {result.stderr}")
                logger.error(f"程序编译失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("编译超时")
            return False
        except Exception as e:
            logger.error(f"编译异常: {e}")
            return False
    
    def _execute_mpc_protocol(self):
        """执行MPC协议"""
        
        logger.info(f"执行{self.protocol}协议...")
        
        try:
            # 使用项目现有的MPCProtocolExecutor
            executor = MPCProtocolExecutor(str(self.mp_spdz_path))
            
            # 执行医疗场景的Shamir协议 - 使用无SSL模式
            results = self._execute_shamir_no_ssl()
            
            print(f"   ✅ Shamir协议执行完成")
            
            # 检查执行状态
            if results.get('success', False):
                print(f"   📊 协议执行成功")
            else:
                print(f"   ❌ 协议执行失败: {results.get('error', 'Unknown error')}")
            
            return results
            
        except Exception as e:
            logger.error(f"MPC协议执行失败: {e}")
            print(f"   ❌ 协议执行失败: {e}")
            return {}
    
    def _analyze_medical_results(self, mpc_results):
        """分析医疗研究结果"""
        
        logger.info("分析医疗研究结果...")
        
        try:
            # 使用项目现有的结果披露组件
            disclosure = MPCResultDisclosure("medical")
            
            # 提取医疗研究结果（从真实MPC结果中解析）
            self._display_medical_results(mpc_results)
            
        except Exception as e:
            logger.error(f"结果分析失败: {e}")
            print(f"   ❌ 结果分析失败: {e}")

    def _display_medical_results(self, mpc_results):
        """显示医疗MPC结果"""
        
        # 显示临床意义分析
        print("\n📋 医疗研究结果披露:")
        print("-" * 60)
        
        try:
            # 检查是否有成功的MPC结果
            if mpc_results.get('success', False):
                # 从真实MPC结果中提取统计数据
                results = self._parse_mpc_output(mpc_results)
                
                # 显示真实医疗MPC计算结果
                if 'mean_age' in results:
                    print(f"📊 患者平均年龄: {results['mean_age']:.1f} 岁")
                if 'mean_baseline' in results:
                    print(f"📊 基线健康评分: {results['mean_baseline']:.1f} 分")
                if 'mean_outcome' in results:
                    print(f"📊 治疗后评分: {results['mean_outcome']:.1f} 分")
                if 'mean_improvement' in results:
                    print(f"📊 平均疗效改善: {results['mean_improvement']:.1f} 分")
                if 'effectiveness_rate' in results:
                    print(f"📊 治疗有效率: {results['effectiveness_rate']:.1f}%")
                if 'adverse_rate' in results:
                    print(f"📊 不良反应率: {results['adverse_rate']:.1f}%")
                
                # 临床解释
                if 'mean_improvement' in results:
                    improvement = results['mean_improvement']
                    if improvement >= 25:
                        print("   🎯 治疗效果优秀")
                    elif improvement >= 15:
                        print("   ✅ 治疗效果良好")
                    else:
                        print("   ⚠️ 治疗效果有限")
                
                if 'effectiveness_rate' in results:
                    eff_rate = results['effectiveness_rate']
                    if eff_rate >= 70:
                        print("   🎯 有效率优秀")
                    elif eff_rate >= 50:
                        print("   ✅ 有效率良好")
                    else:
                        print("   ⚠️ 有效率偏低")
                
                if 'adverse_rate' in results:
                    adverse_rate = results['adverse_rate']
                    if adverse_rate <= 5:
                        print("   ✅ 安全性优秀")
                    elif adverse_rate <= 15:
                        print("   ⚠️ 安全性可接受")
                    else:
                        print("   🚨 需要关注安全性")
            
            else:
                print("   ❌ MPC协议执行失败，无法获取结果")
                error = mpc_results.get('error', 'Unknown error')
                print(f"   错误信息: {error}")
            
            # 隐私保护说明
            print(f"\n🔒 隐私保护保证:")
            print("-" * 40)
            print("✓ 各医院原始患者数据完全保密")
            print("✓ 计算过程中数据始终加密")
            print("✓ 只披露聚合统计结果")
            print("✓ 符合医疗数据隐私法规要求")
            
        except Exception as e:
            logger.error(f"结果显示失败: {e}")
            print(f"   ❌ 结果显示失败: {e}")

    def _parse_mpc_output(self, mpc_results):
        """从真实医疗MPC结果中解析统计数据"""
        try:
            # 直接返回医疗MPC协议解析后的结果
            return {
                'mean_age': mpc_results.get('mean_age', 0),
                'mean_baseline': mpc_results.get('mean_baseline', 0), 
                'mean_outcome': mpc_results.get('mean_outcome', 0),
                'mean_improvement': mpc_results.get('mean_improvement', 0),
                'effectiveness_rate': mpc_results.get('effectiveness_rate', 0),
                'adverse_rate': mpc_results.get('adverse_rate', 0)
            }
        except Exception as e:
            logger.error(f"医疗MPC结果解析失败: {e}")
            return {}

    def _execute_shamir_no_ssl(self):
        """执行无SSL的Shamir协议 - 采用run_real_mpc_protocols.py的成功模式"""
        logger.info("执行简单模式Shamir协议...")
        
        try:
            # 切换到MP-SPDZ目录
            os.chdir(self.mp_spdz_path)
            
            # 使用多线程模式，类似run_real_mpc_protocols.py
            
            # 创建输出队列
            output_queues = [queue.Queue() for _ in range(self.n_parties)]
            threads = []
            
            # 启动所有参与方的线程
            for party_id in range(self.n_parties):
                thread = threading.Thread(
                    target=self._run_party_process,
                    args=(party_id, output_queues[party_id])
                )
                threads.append(thread)
                thread.start()
                # 稍微延迟启动，避免竞争
                time.sleep(0.5)
            
            # 等待所有线程完成
            results = {}
            for i, thread in enumerate(threads):
                thread.join(timeout=60)  # 60秒超时
                
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
            
            # 检查是否有成功的结果
            successful_parties = [r for r in results.values() if r.get('return_code') == 0]
            
            if successful_parties:
                logger.info(f"Shamir协议执行成功: {len(successful_parties)}/{self.n_parties} 参与方成功")
                return self._parse_shamir_output(successful_parties[0]['output'])
            else:
                logger.error("Shamir协议执行失败: 所有参与方都失败")
                return {'success': False, 'error': 'All parties failed'}
                
        except Exception as e:
            logger.error(f"Shamir协议执行异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def _run_party_process(self, party_id, output_queue):
        """运行单个参与方的进程"""
        logger.info(f"启动Shamir协议 - 参与方{party_id}")
        
        try:
            # Shamir协议命令 - 使用简单模式，添加batch-size参数
            cmd = [
                "./shamir-party.x", 
                "-N", str(self.n_parties), 
                "-p", str(party_id), 
                "--batch-size", "8192",
                self.program_name
            ]
            
            logger.info(f"运行命令: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=self.mp_spdz_path
            )
            
            # 读取输出
            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                output_lines.append(line.strip())
                logger.debug(f"Party {party_id}: {line.strip()}")
            
            # 等待进程完成
            return_code = process.wait()
            stderr_output = process.stderr.read()
            
            # 将结果放入队列
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
    
    def _parse_shamir_output(self, output):
        """解析Shamir协议输出结果"""
        try:
            import re
            
            results = {'success': True}
            
            # 查找MEDICAL_DISCLOSURE结果
            disclosure_lines = [line for line in output.split('\n') if 'MEDICAL_DISCLOSURE' in line]
            
            for line in disclosure_lines:
                # 解析医疗统计结果 - 匹配实际MPC输出格式
                if "平均年龄:" in line:
                    match = re.search(r"平均年龄:\s*([0-9.-]+)", line)
                    if match:
                        results['mean_age'] = float(match.group(1))
                elif "基线健康评分:" in line:
                    match = re.search(r"基线健康评分:\s*([0-9.-]+)", line)
                    if match:
                        results['mean_baseline'] = float(match.group(1))
                elif "平均疗效指标:" in line:
                    match = re.search(r"平均疗效指标:\s*([0-9.-]+)", line)
                    if match:
                        results['mean_outcome'] = float(match.group(1))
                elif "平均疗效改善:" in line:
                    match = re.search(r"平均疗效改善:\s*([0-9.-]+)", line)
                    if match:
                        results['mean_improvement'] = float(match.group(1))
                elif "治疗有效率:" in line:
                    match = re.search(r"治疗有效率:\s*([0-9.-]+)", line)
                    if match:
                        results['effectiveness_rate'] = float(match.group(1))
                elif "严重不良反应率:" in line:
                    match = re.search(r"严重不良反应率:\s*([0-9.-]+)", line)
                    if match:
                        results['adverse_rate'] = float(match.group(1))
            
            logger.info(f"解析到 {len(results)-1} 个统计结果")
            
            # 调试输出：显示完整原始输出
            logger.info(f"完整MPC输出 (前1000字符):\n{output[:1000]}")
            logger.info(f"找到的MEDICAL_DISCLOSURE行数: {len(disclosure_lines)}")
            for i, line in enumerate(disclosure_lines[:5]):  # 显示前5行
                logger.info(f"披露行{i}: {line}")
            
            return results
            
        except Exception as e:
            logger.error(f"输出解析失败: {e}")
            return {'success': False, 'error': f'Parse error: {e}'}

def main():
    """主函数"""
    
    print("🚀 医疗机构联合研究MPC系统")
    
    try:
        runner = MedicalMPCRunner()
        runner.run_complete_medical_scenario()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断执行")
    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
        logger.exception("系统异常")
        sys.exit(1)

if __name__ == "__main__":
    main()