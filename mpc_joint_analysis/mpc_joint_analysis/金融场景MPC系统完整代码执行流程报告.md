# 金融场景MPC系统完整代码执行流程报告

## 概述

本报告详细描述了 `mpc_joint_analysis` 项目中金融场景多方安全计算（MPC）的完整执行流程，从用户命令开始到最终结果输出的整个过程。

## 🚀 执行命令

```bash
cd /mnt/c/Users/Lenovo/source/repos/MP-SPDZ/mpc_joint_analysis
python3 run_financial_mpc.py
```

---

## 📋 详细执行流程

### 阶段 1: 系统初始化 (run_financial_mpc.py)

**主入口文件**: `run_financial_mpc.py`

#### 1.1 类初始化
```python
class FinancialMPCRunner:
    def __init__(self, mp_spdz_path="/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        # 设置路径
        self.mp_spdz_path = Path(mp_spdz_path)
        self.project_path = Path(__file__).parent
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化核心组件
        self.data_generator = MPCDataGenerator(seed=42)
        self.program_manager = MPCProgramManager(str(self.mp_spdz_path))
        self.protocol_executor = MPCProtocolExecutor(str(self.mp_spdz_path))
        self.disclosure_manager = MPCResultDisclosure("financial")
```

#### 1.2 配置加载
- **文件**: `scenario_1_financial_config.yaml`
- **目的**: 加载银行配置、协议参数、监管合规要求
- **回退**: 如果配置文件不存在，使用硬编码的默认配置

---

### 阶段 2: 数据生成 (mpc_data_generator.py)

**调用函数**: `generate_financial_data()`

#### 2.1 银行数据生成
```python
def generate_financial_mpc_data(self, n_parties=3, customers_per_bank=100):
    # 为每个银行生成客户数据
    for party_id in range(n_parties):
        # 银行特定配置
        config = bank_configs[party_id]
        
        # 生成100个客户的数据
        for i in range(customers_per_bank):
            customer = {
                'customer_id': f"BANK{party_id}_CUST_{i:05d}",
                'credit_score': float(credit_score),      # X变量
                'income': float(income),                  # Y变量
                'debt_ratio': float(debt_ratio),
                'default_risk': float(default_risk)
            }
```

#### 2.2 输入文件生成
**目标目录**: `/mnt/c/Users/Lenovo/source/repos/MP-SPDZ/Player-Data/`

生成文件：
- `Input-P0-0` (Bank Alpha的数据)
- `Input-P1-0` (Bank Beta的数据)  
- `Input-P2-0` (Bank Gamma的数据)

**数据格式**:
```
# 每个文件包含200行数据
# 前100行: X变量 (信用评分)
759
846
739
...
# 后100行: Y变量 (收入，百美元单位)
835
325
671
...
```

---

### 阶段 3: 程序编译 (mpc_program_manager.py)

**调用函数**: `compile_mpc_program("joint_statistics")`

#### 3.1 程序复制
```python
def copy_program_to_source(self, program_name):
    # 源文件: mpc_joint_analysis/mpc_programs/joint_statistics.mpc
    # 目标: Programs/Source/joint_statistics.mpc
    shutil.copy2(src_path, dst_path)
```

#### 3.2 编译执行
```bash
# 在MP-SPDZ根目录下执行
python3 compile.py joint_statistics -g 64
```

**编译结果**:
- 字节码文件: `Programs/Bytecode/joint_statistics-0.bc`
- 调度文件: `Programs/Schedules/joint_statistics.sch`
- 程序需求: 每方200个整数输入 (100 X + 100 Y)

---

### 阶段 4: MASCOT协议执行 (mpc_executor.py)

**调用函数**: `execute_financial_mpc()`

#### 4.1 协议设置
```python
def setup_mascot_protocol(self, n_parties=3, program="joint_statistics"):
    # 检查字节码文件存在
    bytecode_file = Programs/Bytecode/joint_statistics-0.bc
    # 设置网络配置 (hosts文件)
```

#### 4.2 MASCOT Offline 阶段
```python
def run_mascot_offline_phase(self, n_parties=3):
    # 为每个参与方启动offline进程
    for party_id in range(n_parties):
        cmd = ["./mascot-offline.x", "-N", "3", "-p", str(party_id), "joint_statistics"]
        # 并行执行3个进程
```

**执行时间**: ~59秒  
**生成**: 预处理数据 (三元组、随机数等)

#### 4.3 MASCOT Online 阶段
```python
def run_mascot_online_phase(self, n_parties=3):
    # 为每个参与方启动online进程
    for party_id in range(n_parties):
        cmd = ["./mascot-party.x", "-N", "3", "-p", str(party_id), "joint_statistics"]
        # 并行执行3个进程，读取输入数据进行MPC计算
```

**执行时间**: ~57秒  
**数据传输**: 57GB总量，~20,000通信轮次

---

### 阶段 5: MPC程序执行 (joint_statistics.mpc)

**程序文件**: `Programs/Source/joint_statistics.mpc`

#### 5.1 数据读取
```python
# 从每个参与方读取数据
for party_id in range(n_parties):
    # 读取X变量 (信用评分)
    for i in range(data_size):
        x_val = sint.get_input_from(party_id)
        data_x.append(x_val)
    
    # 读取Y变量 (收入，缩放为千美元)
    for i in range(data_size):
        y_raw = sint.get_input_from(party_id)
        y_scaled = sfix(y_raw) / sfix(10)  # 千美元单位
        data_y.append(y_scaled)
```

#### 5.2 统计计算
```python
# 计算均值
mean_x = sum_x / total_count
mean_y_scaled = sum_y / sfix(total_count)

# 计算方差
variance_x = sum_sq_diff_x / (total_count - 1)
variance_y_scaled = sum_sq_diff_y / sfix(total_count - 1)

# 计算协方差
covariance_scaled = sum_cov / sfix(total_count - 1)
```

#### 5.3 结果输出
```python
print_ln("=== BUSINESS_DISCLOSURE ===")
print_ln("BUSINESS_DISCLOSURE - Mean X (Credit Score): %s", mean_x.reveal())
print_ln("BUSINESS_DISCLOSURE - Mean Y (Income, 1000 USD): %s", mean_y_scaled.reveal())
print_ln("BUSINESS_DISCLOSURE - Variance X: %s", variance_x.reveal())
print_ln("BUSINESS_DISCLOSURE - Variance Y (1000 USD^2): %s", variance_y_scaled.reveal())
print_ln("BUSINESS_DISCLOSURE - Covariance X-Y (Credit*1000USD): %s", covariance_scaled.reveal())
print_ln("=== END_BUSINESS_DISCLOSURE ===")
```

---

### 阶段 6: 结果解析 (mpc_executor.py)

**调用函数**: `parse_mascot_results()`

#### 6.1 输出文件读取
```python
# 读取参与方输出文件
output_files = ["party0_output.txt", "party1_output.txt", "party2_output.txt"]
# 选择第一个成功的参与方输出进行解析
```

#### 6.2 结果提取
```python
# 使用正则表达式解析BUSINESS_DISCLOSURE部分
if "Mean X (Credit Score):" in line:
    parsed_results['mean_credit_score'] = float(match.group(1))
elif "Mean Y (Income" in line:
    parsed_results['mean_income'] = float(match.group(1))
elif "Variance X:" in line:
    parsed_results['variance_credit_score'] = float(match.group(1))
# ... 其他统计量
```

#### 6.3 状态整合
```python
final_results = {
    'protocol_execution': 'SUCCESSFUL',
    'success': True,
    'protocol': 'MASCOT',
    'n_parties': 3,
    'program': 'joint_statistics',
    # ... 合并解析的统计结果
}
```

---

### 阶段 7: 隐私披露处理 (mpc_result_disclosure.py)

**调用函数**: `process_results()`

#### 7.1 披露策略应用
```python
def batch_evaluate_results(self, computed_results, context):
    # 对每个统计结果应用披露策略
    for data_key, computed_value in computed_results.items():
        evaluation = self.evaluate_disclosure(data_key, computed_value, context)
        # 根据隐私风险级别决定是否披露
```

#### 7.2 业务场景策略
```python
financial_policies = {
    "mean_credit_score": DisclosurePolicy(
        disclosure_level=DisclosureLevel.STATISTICAL,
        privacy_risk=PrivacyRisk.LOW,
        business_justification="银行间需要了解整体信用水平以评估系统性风险"
    )
    # ... 其他披露策略
}
```

---

### 阶段 8: 结果展示 (run_financial_mpc.py)

**调用函数**: `display_financial_results()`

#### 8.1 最终报告生成
```python
def display_financial_results(self, results):
    print("🏦 金融机构联合统计分析结果")
    print("📊 协议执行状态: ✅ 成功")
    
    # 显示统计结果
    if 'mean_credit_score' in results:
        print(f"📈 平均信用评分: {results['mean_credit_score']:.2f}")
    
    # 显示隐私保护信息
    print("🔒 隐私保护信息:")
    print("✓ 各银行原始客户数据在整个计算过程中保持私密")
    
    # 显示监管合规信息
    compliance = ["BASEL_III", "GDPR", "PCI_DSS", "SOX"]
    for standard in compliance:
        print(f"✓ {standard} 合规")
```

---

## 📊 最终执行结果

### 统计计算结果
- **平均信用评分**: 725.30
- **平均收入**: 58,898美元 (58.898千美元)
- **信用评分方差**: 5379.33
- **收入方差**: 4,656,090美元² (4656.09千美元²)
- **协方差**: -96,330.2 (负相关关系)

### 协议性能指标
- **总执行时间**: ~116秒 (59秒离线 + 57秒在线)
- **数据传输量**: 57GB
- **通信轮次**: ~20,000轮
- **安全参数**: 40位统计安全参数
- **参与方数量**: 3个银行
- **数据规模**: 每银行100客户，共300客户

---

## 🏗️ 系统架构总结

```
用户命令
    ↓
run_financial_mpc.py (主控制器)
    ↓
├── mpc_data_generator.py (数据生成)
│   └── 生成银行客户数据 → Player-Data/Input-P{0,1,2}-0
    ↓
├── mpc_program_manager.py (程序管理)
│   └── 编译joint_statistics.mpc → Programs/Bytecode/
    ↓
├── mpc_executor.py (协议执行)
│   ├── MASCOT Offline阶段 (预处理)
│   ├── MASCOT Online阶段 (MPC计算)
│   └── 结果解析 → party{0,1,2}_output.txt
    ↓
├── joint_statistics.mpc (MPC程序)
│   ├── 安全读取各方数据
│   ├── 多方统计计算
│   └── 结果披露
    ↓
├── mpc_result_disclosure.py (隐私管理)
│   ├── 应用披露策略
│   └── 生成审计轨迹
    ↓
最终用户报告 (成功/失败状态 + 统计结果)
```

---

## 🔧 核心技术特性

### 安全协议
- **协议**: MASCOT (恶意安全，不诚实多数)
- **安全模型**: 计算安全 + 统计安全参数40
- **隐私保护**: 零知识证明 + 秘密共享

### 数据处理
- **输入格式**: 每方200个整数 (100个X值 + 100个Y值)
- **数值精度**: 64位固定点运算 (sfix)
- **缩放策略**: Y值缩放为千美元单位避免溢出

### 结果披露
- **披露策略**: 基于业务需求的分级披露
- **隐私风险**: LOW/MEDIUM/HIGH三级评估
- **审计轨迹**: 完整的披露决策记录

---

## 📈 业务价值

### 金融机构合作
- **跨行风险评估**: 在保护客户隐私的前提下评估系统性风险
- **监管合规**: 满足BASEL_III、GDPR等监管要求
- **数据协作**: 实现数据价值最大化而不泄露敏感信息

### 统计洞察
- **信用评分分析**: 了解市场整体信用水平
- **收入分布**: 客户收入结构分析
- **相关性分析**: 信用评分与收入的关联关系

这个完整的执行流程确保了金融数据的隐私保护，同时实现了跨机构的安全统计分析。

---

*报告生成时间: 2025-07-24*  
*系统版本: MP-SPDZ + mpc_joint_analysis v1.0*  
*协议类型: MASCOT (Malicious Security)*