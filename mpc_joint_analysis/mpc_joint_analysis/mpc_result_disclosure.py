#!/usr/bin/env python3
"""
MPC结果披露框架
实现灵活的、可配置的MPC结果披露机制
"""

import json
import logging
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class DisclosureLevel(Enum):
    """披露级别枚举"""
    NEVER = "never"              # 从不披露
    AGGREGATE_ONLY = "aggregate" # 仅聚合统计
    STATISTICAL = "statistical"  # 统计指标
    BUSINESS_INSIGHTS = "business" # 业务洞察
    CONDITIONAL = "conditional"   # 条件性披露
    ALWAYS = "always"            # 总是披露

class PrivacyRisk(Enum):
    """隐私风险级别"""
    NONE = 0      # 无风险
    LOW = 1       # 低风险  
    MEDIUM = 2    # 中风险
    HIGH = 3      # 高风险
    CRITICAL = 4  # 关键风险

@dataclass
class DisclosurePolicy:
    """披露策略配置"""
    data_type: str
    disclosure_level: DisclosureLevel
    privacy_risk: PrivacyRisk
    business_justification: str
    conditions: Optional[Dict[str, Any]] = None
    noise_parameters: Optional[Dict[str, float]] = None

class MPCResultDisclosure:
    """MPC结果披露管理器"""
    
    def __init__(self, scenario_type: str):
        self.scenario_type = scenario_type
        self.policies = {}
        self.disclosed_results = {}
        self.audit_trail = []
        
        # 初始化场景特定的披露策略
        self._initialize_policies()
    
    def _initialize_policies(self):
        """初始化披露策略"""
        if self.scenario_type == "financial":
            self.policies = self._get_financial_policies()
        elif self.scenario_type == "medical":
            self.policies = self._get_medical_policies()
        else:
            self.policies = self._get_default_policies()
    
    def _get_financial_policies(self) -> Dict[str, DisclosurePolicy]:
        """金融场景的披露策略"""
        return {
            "mean_credit_score": DisclosurePolicy(
                data_type="aggregate_statistic",
                disclosure_level=DisclosureLevel.STATISTICAL,
                privacy_risk=PrivacyRisk.LOW,
                business_justification="银行间需要了解整体信用水平以评估系统性风险",
                conditions={"min_sample_size": 100}
            ),
            "credit_score_variance": DisclosurePolicy(
                data_type="aggregate_statistic", 
                disclosure_level=DisclosureLevel.STATISTICAL,
                privacy_risk=PrivacyRisk.LOW,
                business_justification="了解客户群体的信用分布差异性"
            ),
            "income_debt_correlation": DisclosurePolicy(
                data_type="correlation_coefficient",
                disclosure_level=DisclosureLevel.BUSINESS_INSIGHTS,
                privacy_risk=PrivacyRisk.LOW,
                business_justification="识别收入与债务比率的关联模式，用于风险建模"
            ),
            "default_probability_mean": DisclosurePolicy(
                data_type="risk_metric",
                disclosure_level=DisclosureLevel.BUSINESS_INSIGHTS,
                privacy_risk=PrivacyRisk.MEDIUM,
                business_justification="评估整体违约风险水平",
                noise_parameters={"epsilon": 0.1}  # 差分隐私参数
            ),
            "high_risk_customer_count": DisclosurePolicy(
                data_type="count_statistic",
                disclosure_level=DisclosureLevel.BUSINESS_INSIGHTS,
                privacy_risk=PrivacyRisk.MEDIUM,
                business_justification="了解高风险客户规模以制定风控策略",
                conditions={"min_count": 10}  # 避免小数量泄露
            ),
            "risk_distribution_percentiles": DisclosurePolicy(
                data_type="distribution_metric",
                disclosure_level=DisclosureLevel.STATISTICAL,
                privacy_risk=PrivacyRisk.LOW,
                business_justification="了解风险分布的分位数情况"
            ),
            "regression_coefficients": DisclosurePolicy(
                data_type="model_parameter",
                disclosure_level=DisclosureLevel.BUSINESS_INSIGHTS,
                privacy_risk=PrivacyRisk.MEDIUM,
                business_justification="风险预测模型的关键参数"
            ),
            "model_r_squared": DisclosurePolicy(
                data_type="model_quality",
                disclosure_level=DisclosureLevel.STATISTICAL,
                privacy_risk=PrivacyRisk.LOW,
                business_justification="模型预测能力评估"
            )
        }
    
    def _get_medical_policies(self) -> Dict[str, DisclosurePolicy]:
        """医疗场景的披露策略"""
        return {
            "patient_count_total": DisclosurePolicy(
                data_type="count_statistic",
                disclosure_level=DisclosureLevel.STATISTICAL,
                privacy_risk=PrivacyRisk.LOW,
                business_justification="研究样本量信息对于统计检验力计算必要",
                conditions={"min_count": 50}
            ),
            "age_mean": DisclosurePolicy(
                data_type="demographic_statistic",
                disclosure_level=DisclosureLevel.STATISTICAL,
                privacy_risk=PrivacyRisk.LOW,
                business_justification="人群年龄基线对于临床研究标准化必要"
            ),
            "biomarker_correlation_matrix": DisclosurePolicy(
                data_type="correlation_analysis",
                disclosure_level=DisclosureLevel.BUSINESS_INSIGHTS,
                privacy_risk=PrivacyRisk.LOW,
                business_justification="生物标志物间相关性分析支持疾病机制研究"
            ),
            "treatment_effectiveness_mean": DisclosurePolicy(
                data_type="efficacy_metric",
                disclosure_level=DisclosureLevel.BUSINESS_INSIGHTS,
                privacy_risk=PrivacyRisk.MEDIUM,
                business_justification="治疗效果的平均水平评估",
                noise_parameters={"epsilon": 0.2}
            ),
            "adverse_event_rate": DisclosurePolicy(
                data_type="safety_metric",
                disclosure_level=DisclosureLevel.CONDITIONAL,
                privacy_risk=PrivacyRisk.HIGH,
                business_justification="安全性评估的关键指标",
                conditions={"min_events": 5, "regulatory_approval": True}
            ),
            "survival_curve_parameters": DisclosurePolicy(
                data_type="survival_analysis",
                disclosure_level=DisclosureLevel.BUSINESS_INSIGHTS,
                privacy_risk=PrivacyRisk.MEDIUM,
                business_justification="生存分析参数用于疗效评估"
            ),
            "subgroup_analysis_results": DisclosurePolicy(
                data_type="subgroup_metric",
                disclosure_level=DisclosureLevel.CONDITIONAL,
                privacy_risk=PrivacyRisk.HIGH,
                business_justification="亚组分析支持精准医疗",
                conditions={"min_subgroup_size": 30}
            )
        }
    
    def _get_default_policies(self) -> Dict[str, DisclosurePolicy]:
        """默认披露策略"""
        return {
            "aggregate_statistics": DisclosurePolicy(
                data_type="general_aggregate",
                disclosure_level=DisclosureLevel.STATISTICAL,
                privacy_risk=PrivacyRisk.LOW,
                business_justification="通用聚合统计信息"
            )
        }
    
    def evaluate_disclosure(self, data_key: str, computed_value: Any, 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """评估是否应该披露某个计算结果"""
        
        if data_key not in self.policies:
            logger.warning(f"No disclosure policy found for {data_key}")
            return {"should_disclose": False, "reason": "no_policy"}
        
        policy = self.policies[data_key]
        context = context or {}
        
        # 评估披露条件
        evaluation_result = {
            "data_key": data_key,
            "should_disclose": False,
            "disclosure_value": None,
            "privacy_risk": policy.privacy_risk.name,
            "business_justification": policy.business_justification,
            "conditions_met": True,
            "conditions_checked": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 检查条件
        if policy.conditions:
            for condition_key, condition_value in policy.conditions.items():
                condition_met = self._check_condition(
                    condition_key, condition_value, computed_value, context
                )
                evaluation_result["conditions_checked"].append({
                    "condition": condition_key,
                    "required": condition_value,
                    "met": condition_met
                })
                if not condition_met:
                    evaluation_result["conditions_met"] = False
        
        # 根据披露级别决定是否披露
        if evaluation_result["conditions_met"]:
            if policy.disclosure_level == DisclosureLevel.ALWAYS:
                evaluation_result["should_disclose"] = True
                evaluation_result["disclosure_value"] = computed_value
            elif policy.disclosure_level == DisclosureLevel.NEVER:
                evaluation_result["should_disclose"] = False
            else:
                # 其他级别根据隐私风险和业务需求综合决定
                evaluation_result["should_disclose"] = True
                
                # 应用隐私保护技术
                if policy.noise_parameters:
                    evaluation_result["disclosure_value"] = self._apply_privacy_protection(
                        computed_value, policy.noise_parameters
                    )
                else:
                    evaluation_result["disclosure_value"] = computed_value
        
        # 记录审计轨迹
        self._log_disclosure_decision(evaluation_result)
        
        return evaluation_result
    
    def _check_condition(self, condition_key: str, condition_value: Any, 
                        computed_value: Any, context: Dict[str, Any]) -> bool:
        """检查披露条件是否满足"""
        
        if condition_key == "min_sample_size":
            sample_size = context.get("sample_size", 0)
            return sample_size >= condition_value
        
        elif condition_key == "min_count":
            if isinstance(computed_value, (int, float)):
                return computed_value >= condition_value
            return False
        
        elif condition_key == "min_events":
            event_count = context.get("event_count", 0)
            return event_count >= condition_value
        
        elif condition_key == "min_subgroup_size":
            subgroup_size = context.get("subgroup_size", 0)
            return subgroup_size >= condition_value
        
        elif condition_key == "regulatory_approval":
            return context.get("regulatory_approved", False) == condition_value
        
        return True
    
    def _apply_privacy_protection(self, value: Any, 
                                protection_params: Dict[str, float]) -> Any:
        """应用隐私保护技术（如差分隐私）"""
        
        if "epsilon" in protection_params:
            # 应用拉普拉斯机制差分隐私
            epsilon = protection_params["epsilon"]
            sensitivity = protection_params.get("sensitivity", 1.0)
            
            if isinstance(value, (int, float)):
                # 添加拉普拉斯噪声
                scale = sensitivity / epsilon
                noise = np.random.laplace(0, scale)
                protected_value = value + noise
                
                logger.info(f"Applied DP noise: original={value}, "
                           f"protected={protected_value}, epsilon={epsilon}")
                
                return protected_value
        
        return value
    
    def _log_disclosure_decision(self, evaluation_result: Dict[str, Any]):
        """记录披露决策的审计轨迹"""
        audit_entry = {
            "timestamp": evaluation_result["timestamp"],
            "data_key": evaluation_result["data_key"],
            "decision": "disclosed" if evaluation_result["should_disclose"] else "protected",
            "privacy_risk": evaluation_result["privacy_risk"],
            "conditions_met": evaluation_result["conditions_met"],
            "business_justification": evaluation_result["business_justification"]
        }
        
        self.audit_trail.append(audit_entry)
        
        # 记录到日志
        logger.info(f"Disclosure decision: {audit_entry}")
    
    def batch_evaluate_results(self, computed_results: Dict[str, Any],
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """批量评估多个计算结果的披露"""
        
        disclosed_results = {}
        evaluation_summary = {
            "total_computed": len(computed_results),
            "total_disclosed": 0,
            "total_protected": 0,
            "disclosure_decisions": {}
        }
        
        for data_key, computed_value in computed_results.items():
            evaluation = self.evaluate_disclosure(data_key, computed_value, context)
            
            if evaluation["should_disclose"]:
                disclosed_results[data_key] = evaluation["disclosure_value"]
                evaluation_summary["total_disclosed"] += 1
            else:
                evaluation_summary["total_protected"] += 1
            
            evaluation_summary["disclosure_decisions"][data_key] = evaluation
        
        return {
            "disclosed_results": disclosed_results,
            "evaluation_summary": evaluation_summary,
            "audit_trail": self.audit_trail
        }
    
    def generate_disclosure_report(self) -> str:
        """生成披露决策报告"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = f"""
# MPC结果披露报告

**生成时间**: {datetime.now().isoformat()}
**场景类型**: {self.scenario_type}
**披露策略数量**: {len(self.policies)}

## 披露策略概览

"""
        
        for data_key, policy in self.policies.items():
            report += f"""
### {data_key}
- **数据类型**: {policy.data_type}
- **披露级别**: {policy.disclosure_level.value}
- **隐私风险**: {policy.privacy_risk.name}
- **业务理由**: {policy.business_justification}
"""
            if policy.conditions:
                report += f"- **披露条件**: {policy.conditions}\n"
            if policy.noise_parameters:
                report += f"- **隐私保护**: {policy.noise_parameters}\n"
        
        report += f"""
## 审计轨迹

总决策数量: {len(self.audit_trail)}

"""
        
        for entry in self.audit_trail[-10:]:  # 显示最近10个决策
            report += f"""
### {entry['timestamp']}
- **数据项**: {entry['data_key']}
- **决策**: {entry['decision']}
- **隐私风险**: {entry['privacy_risk']}
- **条件满足**: {entry['conditions_met']}
- **业务理由**: {entry['business_justification']}
"""
        
        return report
    
    def export_audit_trail(self, filepath: str):
        """导出审计轨迹到文件"""
        audit_data = {
            "scenario_type": self.scenario_type,
            "export_timestamp": datetime.now().isoformat(),
            "policies": {k: {
                "data_type": v.data_type,
                "disclosure_level": v.disclosure_level.value,
                "privacy_risk": v.privacy_risk.name,
                "business_justification": v.business_justification,
                "conditions": v.conditions,
                "noise_parameters": v.noise_parameters
            } for k, v in self.policies.items()},
            "audit_trail": self.audit_trail
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Audit trail exported to: {filepath}")

def create_disclosure_manager(scenario_type: str) -> MPCResultDisclosure:
    """工厂函数：创建披露管理器"""
    return MPCResultDisclosure(scenario_type)

# 使用示例
if __name__ == "__main__":
    # 创建金融场景的披露管理器
    financial_disclosure = create_disclosure_manager("financial")
    
    # 模拟一些计算结果
    mock_results = {
        "mean_credit_score": 728.5,
        "credit_score_variance": 85.2,
        "income_debt_correlation": 0.65,
        "default_probability_mean": 0.23,
        "high_risk_customer_count": 45
    }
    
    context = {
        "sample_size": 150,
        "event_count": 45
    }
    
    # 批量评估披露
    disclosure_results = financial_disclosure.batch_evaluate_results(mock_results, context)
    
    print("披露的结果:")
    for key, value in disclosure_results["disclosed_results"].items():
        print(f"  {key}: {value}")
    
    print(f"\n披露汇总: {disclosure_results['evaluation_summary']['total_disclosed']}/")
    print(f"{disclosure_results['evaluation_summary']['total_computed']} 项结果被披露")