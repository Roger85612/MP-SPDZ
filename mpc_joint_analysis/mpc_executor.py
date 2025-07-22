#!/usr/bin/env python3
"""
真正的MP-SPDZ协议执行器
执行真实的多方安全计算协议
"""

import subprocess
import threading
import time
import os
import signal
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

logger = logging.getLogger(__name__)

class MPCProtocolExecutor:
    """MP-SPDZ协议执行器"""
    
    def __init__(self, mp_spdz_path: str = "/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        self.mp_spdz_path = Path(mp_spdz_path)
        self.processes = []
        self.results = {}
        
    def setup_mascot_protocol(self, n_parties: int = 3, program: str = "financial_risk_analysis"):
        """设置MASCOT协议环境"""
        
        # 切换到MP-SPDZ目录
        os.chdir(self.mp_spdz_path)
        
        # 检查程序是否已编译
        bytecode_file = self.mp_spdz_path / "Programs" / "Bytecode" / f"{program}-0.bc"
        if not bytecode_file.exists():
            raise FileNotFoundError(f"Program {program} not compiled. Run: python3 compile.py {program}")
        
        logger.info(f"Setting up MASCOT protocol for {n_parties} parties")
        logger.info(f"Program: {program}")
        logger.info(f"Bytecode: {bytecode_file}")
        
        return True
    
    def run_mascot_offline_phase(self, n_parties: int = 3, program: str = "financial_risk_analysis"):
        """运行MASCOT协议的预处理阶段（离线阶段）"""
        
        logger.info("Starting MASCOT offline phase...")
        
        try:
            # 正确的MASCOT预处理命令格式: ./mascot-offline.x [options] <program>
            cmd = [
                "./mascot-offline.x",
                "-N", str(n_parties),
                "-p", "0",  # 使用party 0进行预处理
                program
            ]
            
            logger.info(f"Running offline phase: {' '.join(cmd)}")
            
            # 运行预处理阶段
            offline_process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 增加超时时间到2分钟
                cwd=self.mp_spdz_path
            )
            
            if offline_process.returncode == 0:
                logger.info("MASCOT offline phase completed successfully")
                return True
            else:
                logger.error(f"MASCOT offline phase failed with code {offline_process.returncode}")
                logger.error(f"Stderr: {offline_process.stderr}")
                logger.error(f"Stdout: {offline_process.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("MASCOT offline phase timed out")
            return False
        except Exception as e:
            logger.error(f"MASCOT offline phase failed: {e}")
            return False
    
    def run_mascot_online_phase(self, n_parties: int = 3, program: str = "financial_risk_analysis") -> Dict:
        """运行MASCOT协议的在线阶段（真正的MPC计算）"""
        
        logger.info("Starting MASCOT online phase...")
        
        # 为每个参与方启动进程
        processes = []
        output_files = []
        
        for party_id in range(n_parties):
            # 每个参与方的输出文件
            output_file = f"party{party_id}_output.txt"
            output_files.append(output_file)
            
            # MASCOT在线阶段命令 - 修正参数格式
            cmd = [
                "./mascot-party.x",
                "-N", str(n_parties),
                "-p", str(party_id),
                program
            ]
            
            logger.info(f"Starting Party {party_id}: {' '.join(cmd)}")
            
            # 启动参与方进程
            with open(output_file, 'w') as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    cwd=self.mp_spdz_path,
                    text=True
                )
                processes.append((party_id, process, output_file))
        
        # 等待所有进程完成
        results = {}
        for party_id, process, output_file in processes:
            try:
                # 等待最多60秒
                stdout, stderr = process.communicate(timeout=60)
                returncode = process.returncode
                
                # 读取输出
                with open(output_file, 'r') as f:
                    output = f.read()
                
                results[party_id] = {
                    'returncode': returncode,
                    'output': output,
                    'stderr': stderr,
                    'success': returncode == 0
                }
                
                logger.info(f"Party {party_id} finished with return code {returncode}")
                
            except subprocess.TimeoutExpired:
                logger.warning(f"Party {party_id} timed out")
                process.kill()
                results[party_id] = {
                    'returncode': -1,
                    'output': "Process timed out",
                    'stderr': "Timeout",
                    'success': False
                }
        
        return results
    
    def parse_mpc_results(self, results: Dict) -> Dict:
        """解析MPC计算结果"""
        
        logger.info("Parsing MPC computation results...")
        
        # 寻找成功完成的参与方结果
        successful_results = [r for r in results.values() if r['success']]
        
        if not successful_results:
            logger.error("No successful MPC results found")
            return {
                'protocol_execution': 'FAILED',
                'success': False,
                'error': 'All MASCOT parties failed to execute',
                'note': '真实MASCOT协议执行失败 - 未使用模拟数据'
            }
        
        # 从第一个成功的参与方获取结果
        primary_result = successful_results[0]
        output_text = primary_result['output']
        
        # 打印完整输出以便调试
        logger.info(f"Full MPC output text:\n{output_text}")
        
        # 解析统计结果
        parsed_results = {}
        
        try:
            # 解析BUSINESS_DISCLOSURE标记的结果
            disclosure_lines = [line for line in output_text.split('\n') if 'BUSINESS_DISCLOSURE' in line]
            logger.info(f"Found {len(disclosure_lines)} business disclosure lines")
            
            for line in disclosure_lines:
                logger.info(f"Processing disclosure line: {line}")
                
                # 解析不同类型的披露
                if "Total:" in line:
                    total_match = re.search(r"Total:\s*([\d.-]+)", line)
                    if total_match:
                        parsed_results['total_customers'] = int(float(total_match.group(1)))
                
                elif "Mean:" in line:
                    mean_match = re.search(r"Mean:\s*([\d.-]+)", line)
                    if mean_match:
                        parsed_results['mean_value'] = float(mean_match.group(1))
                
                elif "Average Credit Score:" in line:
                    credit_match = re.search(r"Average Credit Score:\s*([\d.-]+)", line)
                    if credit_match:
                        parsed_results['mean_credit_score'] = float(credit_match.group(1))
                
                elif "Average Default Risk:" in line:
                    risk_match = re.search(r"Average Default Risk:\s*([\d.-]+)", line)
                    if risk_match:
                        parsed_results['mean_default_risk'] = float(risk_match.group(1))
                
                elif "High Risk Customers:" in line:
                    high_risk_match = re.search(r"High Risk Customers:\s*(\d+)", line)
                    if high_risk_match:
                        parsed_results['high_risk_customers'] = int(high_risk_match.group(1))
            
            # 中文解析作为备用
            if not parsed_results:
                # 解析中文输出
                if "总客户数:" in output_text:
                    total_customers = re.search(r"总客户数:\s*(\d+)", output_text)
                    if total_customers:
                        parsed_results['total_customers'] = int(total_customers.group(1))
                
                if "平均信用评分:" in output_text:
                    avg_credit = re.search(r"平均信用评分:\s*([\d.-]+)", output_text)
                    if avg_credit:
                        parsed_results['mean_credit_score'] = float(avg_credit.group(1))
            
            logger.info(f"Successfully parsed MPC results: {parsed_results}")
            
        except Exception as e:
            logger.error(f"Error parsing results: {e}")
            return {
                'protocol_execution': 'PARSING_FAILED',
                'success': False,
                'error': f'Failed to parse MASCOT output: {str(e)}',
                'note': '协议执行成功但结果解析失败 - 未使用模拟数据'
            }
        
        # 如果解析失败，报告解析问题
        if not parsed_results:
            logger.warning("Could not parse MPC results")
            return {
                'protocol_execution': 'PARSING_FAILED',
                'success': False,
                'error': 'No parseable results found in MASCOT output',
                'note': '协议执行成功但无法解析结果 - 未使用模拟数据'
            }
        
        return parsed_results
    
# 已移除generate_fallback_results函数 - 不再提供模拟数据
    
    def execute_financial_mpc(self, n_parties: int = 3, program: str = "financial_risk_analysis") -> Dict:
        """执行完整的金融MPC计算流程"""
        
        logger.info("=== Starting Financial MPC Execution ===")
        
        try:
            # 1. 设置协议环境
            self.setup_mascot_protocol(n_parties, program)
            
            # 2. 运行离线阶段
            offline_success = self.run_mascot_offline_phase(n_parties, program)
            if not offline_success:
                logger.error("MASCOT offline phase failed, cannot proceed to online phase")
                return {
                    'protocol_execution': 'FAILED',
                    'protocol': 'MASCOT',
                    'n_parties': n_parties,
                    'program': program,
                    'success': False,
                    'error': 'MASCOT offline phase failed',
                    'note': 'MASCOT协议预处理阶段失败 - 未使用模拟数据'
                }
            
            # 3. 运行在线阶段
            online_results = self.run_mascot_online_phase(n_parties, program)
            
            # 4. 解析结果
            parsed_results = self.parse_mpc_results(online_results)
            
            # 5. 添加元数据
            parsed_results.update({
                'protocol': 'MASCOT',
                'n_parties': n_parties,
                'program': program,
                'offline_phase': offline_success,
                'online_phase_success': any(r['success'] for r in online_results.values())
            })
            
            logger.info("=== Financial MPC Execution Completed ===")
            return parsed_results
            
        except Exception as e:
            logger.error(f"MPC execution failed: {e}")
            # 不返回模拟数据，直接报告协议执行失败
            return {
                'protocol_execution': 'FAILED',
                'protocol': 'MASCOT',
                'n_parties': n_parties,
                'program': program,
                'success': False,
                'error': f'MASCOT protocol execution failed: {str(e)}',
                'note': '真实MASCOT协议执行失败 - 未使用模拟数据'
            }
    
    def run_shamir_protocol(self, n_parties: int = 3, program: str = "joint_statistics") -> Dict:
        """运行真实的Shamir协议（非emulation）- 解决SSL握手冲突"""
        
        logger.info(f"Starting REAL Shamir protocol for {program}...")
        
        # 检查shamir-party.x是否存在
        shamir_executable = "./shamir-party.x"
        shamir_full_path = self.mp_spdz_path / "shamir-party.x"
        if not shamir_full_path.exists():
            logger.error(f"Shamir executable not found: {shamir_full_path}")
            return {'protocol_execution': 'FAILED', 'error': 'Shamir executable not found', 'success': False}
        
        # 切换到MP-SPDZ目录
        os.chdir(self.mp_spdz_path)
        
        # 方式1: 尝试使用Server.x协调器启动
        logger.info("Attempting Shamir protocol with Server.x coordinator...")
        results = self._run_shamir_with_coordinator(n_parties, program)
        
        # 检查是否有成功的结果
        if any(r.get('success', False) for r in results.values()):
            logger.info("Shamir protocol with coordinator succeeded!")
            return results
        
        # 方式2: 如果协调器失败，尝试序列化启动
        logger.info("Coordinator failed, trying sequential startup with port separation...")
        results = self._run_shamir_sequential(n_parties, program)
        
        return results
    
    def _run_shamir_with_coordinator(self, n_parties: int, program: str) -> Dict:
        """使用Server.x协调器运行Shamir协议"""
        
        # 启动Server.x协调器
        server_process = None
        try:
            server_cmd = ["./Server.x", str(n_parties), "5000"]
            logger.info(f"Starting Server.x coordinator: {' '.join(server_cmd)}")
            
            server_process = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.mp_spdz_path,
                text=True
            )
            
            # 等待服务器启动
            time.sleep(3)
            
            # 检查服务器是否还在运行
            if server_process.poll() is not None:
                logger.warning("Server.x coordinator exited early")
                return self._run_shamir_direct(n_parties, program)
            
            # 启动各参与方
            processes = []
            
            for party_id in range(n_parties):
                output_file = self.mp_spdz_path / f"shamir_party{party_id}_output.txt"
                
                cmd = [
                    "./shamir-party.x",
                    "-h", "localhost",
                    "-p", str(party_id),
                    "-N", str(n_parties),
                    program
                ]
                
                logger.info(f"Starting Shamir Party {party_id} with coordinator")
                
                with open(output_file, 'w') as f:
                    process = subprocess.Popen(
                        cmd,
                        stdout=f,
                        stderr=subprocess.STDOUT,
                        cwd=self.mp_spdz_path,
                        text=True
                    )
                    processes.append((party_id, process, output_file))
                
                # 序列化启动，减少冲突
                time.sleep(2)
            
            # 等待所有进程完成
            results = {}
            for party_id, process, output_file in processes:
                try:
                    returncode = process.wait(timeout=90)
                    
                    with open(output_file, 'r') as f:
                        output = f.read()
                    
                    results[party_id] = {
                        'returncode': returncode,
                        'output': output,
                        'stderr': '',
                        'success': returncode == 0
                    }
                    
                    logger.info(f"Coordinated Shamir Party {party_id} finished with code {returncode}")
                    if returncode == 0:
                        logger.info(f"Party {party_id} SUCCESS - output length: {len(output)}")
                    else:
                        logger.warning(f"Party {party_id} FAILED - first 200 chars: {output[:200]}")
                    
                except subprocess.TimeoutExpired:
                    logger.warning(f"Shamir Party {party_id} timed out")
                    process.kill()
                    process.wait()
                    results[party_id] = {
                        'returncode': -1,
                        'output': f"Party {party_id} timed out during execution",
                        'stderr': "Timeout",
                        'success': False
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Coordinator execution failed: {e}")
            return {i: {'returncode': -1, 'output': f"Coordinator error: {e}", 'success': False} for i in range(n_parties)}
        finally:
            # 清理Server.x进程
            if server_process and server_process.poll() is None:
                try:
                    server_process.terminate()
                    server_process.wait(timeout=5)
                except:
                    server_process.kill()
    
    def _run_shamir_sequential(self, n_parties: int, program: str) -> Dict:
        """序列化启动Shamir协议，使用端口分离避免冲突"""
        
        processes = []
        results = {}
        
        # 清理之前的输出文件
        for party_id in range(n_parties):
            output_file = self.mp_spdz_path / f"shamir_party{party_id}_output.txt"
            if output_file.exists():
                output_file.unlink()
        
        # 按顺序启动，使用不同端口基数
        for party_id in range(n_parties):
            output_file = self.mp_spdz_path / f"shamir_party{party_id}_output.txt"
            port_base = 5000 + party_id * 100  # 给每方分配足够的端口空间
            
            cmd = [
                "./shamir-party.x",
                "-N", str(n_parties),
                "-p", str(party_id),
                "-pn", str(port_base),  # 使用不同的端口基数
                program
            ]
            
            logger.info(f"Starting sequential Shamir Party {party_id} on port base {port_base}")
            
            try:
                with open(output_file, 'w') as f:
                    process = subprocess.Popen(
                        cmd,
                        stdout=f,
                        stderr=subprocess.STDOUT,
                        cwd=self.mp_spdz_path,
                        text=True
                    )
                    processes.append((party_id, process, output_file))
                
                # 更长的启动间隔，确保前一个进程完全启动
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Failed to start sequential party {party_id}: {e}")
                results[party_id] = {
                    'returncode': -1,
                    'output': f"Failed to start party {party_id}: {e}",
                    'stderr': str(e),
                    'success': False
                }
        
        # 等待所有进程完成
        for party_id, process, output_file in processes:
            try:
                returncode = process.wait(timeout=120)  # 更长的超时时间
                
                with open(output_file, 'r') as f:
                    output = f.read()
                
                results[party_id] = {
                    'returncode': returncode,
                    'output': output,
                    'stderr': '',
                    'success': returncode == 0
                }
                
                logger.info(f"Sequential Shamir Party {party_id} finished with code {returncode}")
                if returncode == 0:
                    logger.info(f"Party {party_id} SUCCESS - output length: {len(output)}")
                else:
                    logger.warning(f"Party {party_id} FAILED - error preview: {output[:300]}")
                
            except subprocess.TimeoutExpired:
                logger.warning(f"Sequential Shamir Party {party_id} timed out")
                process.kill()
                process.wait()
                results[party_id] = {
                    'returncode': -1,
                    'output': f"Party {party_id} timed out during sequential execution",
                    'stderr': "Timeout",
                    'success': False
                }
        
        return results
    
    def _run_shamir_direct(self, n_parties: int, program: str) -> Dict:
        """直接启动Shamir协议（无协调器）"""
        
        processes = []
        results = {}
        
        for party_id in range(n_parties):
            output_file = self.mp_spdz_path / f"shamir_party{party_id}_output.txt"
            
            cmd = [
                "./shamir-party.x",
                "-N", str(n_parties),
                "-p", str(party_id),
                program
            ]
            
            logger.info(f"Starting direct Shamir Party {party_id}")
            
            with open(output_file, 'w') as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=self.mp_spdz_path,
                    text=True
                )
                processes.append((party_id, process, output_file))
            
            time.sleep(1)  # 短间隔
        
        # 等待进程完成
        for party_id, process, output_file in processes:
            try:
                returncode = process.wait(timeout=60)
                
                with open(output_file, 'r') as f:
                    output = f.read()
                
                results[party_id] = {
                    'returncode': returncode,
                    'output': output,
                    'stderr': '',
                    'success': returncode == 0
                }
                
                logger.info(f"Direct Shamir Party {party_id} finished with code {returncode}")
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                results[party_id] = {
                    'returncode': -1,
                    'output': f"Party {party_id} timed out in direct mode",
                    'stderr': "Timeout",
                    'success': False
                }
        
        return results
    
    def parse_shamir_results(self, results: Dict) -> Dict:
        """解析Shamir协议的MPC计算结果 - 不使用模拟数据fallback"""
        
        logger.info("Parsing Shamir MPC computation results...")
        
        # 寻找成功完成的参与方结果
        successful_results = [r for r in results.values() if r.get('success', False)]
        
        if not successful_results:
            logger.error("No successful Shamir MPC results found")
            # 分析失败原因
            failure_reasons = []
            for party_id, result in results.items():
                if not result.get('success', False):
                    output = result.get('output', '')
                    if 'SSL error' in output:
                        failure_reasons.append(f"Party {party_id}: SSL handshake failed")
                    elif 'timeout' in output.lower():
                        failure_reasons.append(f"Party {party_id}: Execution timeout")
                    elif result.get('returncode', 0) != 0:
                        failure_reasons.append(f"Party {party_id}: Process failed (code {result.get('returncode')})")
                    else:
                        failure_reasons.append(f"Party {party_id}: Unknown failure")
            
            return {
                'protocol_execution': 'FAILED', 
                'success': False,
                'error': 'Real Shamir protocol execution failed',
                'failure_details': failure_reasons,
                'note': '真实MPC协议执行失败 - 未使用模拟数据'
            }
        
        # 从成功的参与方获取结果
        primary_result = successful_results[0]
        output_text = primary_result.get('output', '')
        
        # 打印完整输出以便调试
        logger.info(f"Full Shamir MPC output text (length: {len(output_text)}):\n{output_text[:1000]}...")
        
        # 解析统计结果
        parsed_results = {'protocol_execution': 'SUCCESS', 'success': True}
        
        try:
            # 解析BUSINESS_DISCLOSURE标记的结果
            disclosure_lines = [line for line in output_text.split('\n') if 'BUSINESS_DISCLOSURE' in line]
            logger.info(f"Found {len(disclosure_lines)} business disclosure lines")
            
            if disclosure_lines:
                logger.info("Processing reveal mechanism outputs...")
                for line in disclosure_lines:
                    logger.info(f"Processing disclosure line: {line}")
                    
                    # 解析不同类型的披露
                    if "Mean X:" in line:
                        mean_x_match = re.search(r"Mean X:\s*([0-9.-]+)", line)
                        if mean_x_match:
                            parsed_results['mean_x'] = float(mean_x_match.group(1))
                    
                    elif "Mean Y:" in line:
                        mean_y_match = re.search(r"Mean Y:\s*([0-9.-]+)", line)
                        if mean_y_match:
                            parsed_results['mean_y'] = float(mean_y_match.group(1))
                    
                    elif "Variance X:" in line:
                        var_x_match = re.search(r"Variance X:\s*([0-9.-]+)", line)
                        if var_x_match:
                            parsed_results['variance_x'] = float(var_x_match.group(1))
                    
                    elif "Variance Y:" in line:
                        var_y_match = re.search(r"Variance Y:\s*([0-9.-]+)", line)
                        if var_y_match:
                            parsed_results['variance_y'] = float(var_y_match.group(1))
                    
                    elif "Correlation X-Y:" in line:
                        corr_match = re.search(r"Correlation X-Y:\s*([0-9.-]+)", line)
                        if corr_match:
                            parsed_results['correlation_xy'] = float(corr_match.group(1))
                    
                    elif "Beta Coefficient:" in line:
                        beta_match = re.search(r"Beta Coefficient:\s*([0-9.-]+)", line)
                        if beta_match:
                            parsed_results['beta_coefficient'] = float(beta_match.group(1))
                
                logger.info(f"Successfully parsed {len(parsed_results)-2} real MPC results from reveal mechanism")
            else:
                logger.warning("No BUSINESS_DISCLOSURE lines found in output, but protocol succeeded")
                parsed_results['note'] = 'Protocol executed successfully but no reveal outputs found'
            
        except Exception as e:
            logger.error(f"Error parsing Shamir results: {e}")
            return {
                'protocol_execution': 'PARSING_FAILED',
                'success': False,
                'error': f'Failed to parse protocol output: {e}',
                'raw_output_length': len(output_text),
                'note': '真实协议执行成功但结果解析失败'
            }
        
        return parsed_results
    
# 已移除generate_medical_fallback_results函数 - 不再提供模拟数据
    
    def execute_medical_mpc(self, n_parties: int = 3, program: str = "joint_statistics") -> Dict:
        """执行完整的医疗MPC计算流程（使用Shamir协议）- 无模拟数据fallback"""
        
        logger.info("=== Starting Medical MPC Execution (Shamir Protocol) ===")
        
        try:
            # 1. 检查程序是否已编译
            bytecode_file = self.mp_spdz_path / "Programs" / "Bytecode" / f"{program}-0.bc"
            if not bytecode_file.exists():
                error_msg = f"Program {program} not compiled. Run: python3 compile.py {program}"
                logger.error(error_msg)
                return {
                    'protocol_execution': 'FAILED',
                    'protocol': 'Shamir',
                    'n_parties': n_parties,
                    'program': program,
                    'error': error_msg,
                    'success': False,
                    'note': 'MPC程序编译检查失败'
                }
            
            # 2. 运行Shamir协议
            logger.info(f"Executing real Shamir protocol for {program}...")
            shamir_results = self.run_shamir_protocol(n_parties, program)
            
            # 3. 检查协议执行状态
            execution_success = any(r.get('success', False) for r in shamir_results.values() if isinstance(r, dict))
            
            if not execution_success:
                # 协议执行失败，分析原因
                logger.error("Shamir protocol execution failed for all parties")
                failure_analysis = {
                    'protocol_execution': 'FAILED',
                    'protocol': 'Shamir',
                    'n_parties': n_parties,
                    'program': program,
                    'success': False,
                    'error': 'All parties failed to execute Shamir protocol',
                    'party_results': shamir_results,
                    'note': '真实Shamir协议执行失败 - 未使用模拟数据'
                }
                
                # 添加详细的失败分析
                failure_details = []
                for party_id, result in shamir_results.items():
                    if isinstance(result, dict):
                        output = result.get('output', '')
                        if 'SSL' in output:
                            failure_details.append(f"Party {party_id}: SSL握手失败")
                        elif 'timeout' in output.lower():
                            failure_details.append(f"Party {party_id}: 执行超时")
                        else:
                            failure_details.append(f"Party {party_id}: 进程失败 (code {result.get('returncode', 'unknown')})")
                
                failure_analysis['failure_details'] = failure_details
                logger.info("=== Medical MPC Execution Failed ===")
                return failure_analysis
            
            # 4. 解析结果
            logger.info("Protocol executed successfully, parsing results...")
            parsed_results = self.parse_shamir_results(shamir_results)
            
            # 5. 添加元数据
            parsed_results.update({
                'protocol': 'Shamir',
                'n_parties': n_parties,
                'program': program,
                'execution_success': True
            })
            
            logger.info("=== Medical MPC Execution Completed Successfully ===")
            return parsed_results
            
        except Exception as e:
            logger.error(f"Medical MPC execution failed with exception: {e}")
            return {
                'protocol_execution': 'EXCEPTION',
                'protocol': 'Shamir',
                'n_parties': n_parties,
                'program': program,
                'error': str(e),
                'success': False,
                'note': '医疗MPC执行遇到异常 - 未使用模拟数据'
            }

    def cleanup(self):
        """清理资源"""
        
        # 终止所有进程
        for process in self.processes:
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        self.processes.clear()
        logger.info("Cleaned up MPC processes")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 执行MPC
    executor = MPCProtocolExecutor()
    
    try:
        results = executor.execute_financial_mpc()
        print("\n🔐 MPC Execution Results:")
        for key, value in results.items():
            print(f"  {key}: {value}")
    
    finally:
        executor.cleanup()