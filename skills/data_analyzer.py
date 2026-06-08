"""企业级数据分析工具 - 支持数据统计、趋势分析、异常检测"""
import json
import statistics
from typing import Optional
from langchain_core.tools import tool


@tool
def calculate_statistics(numbers_str: str) -> str:
    """计算一组数字的统计信息（均值、中位数、标准差、最大/最小值等）。
    
    Args:
        numbers_str: 逗号分隔的数字字符串，如 "10,20,30,40,50"
    """
    try:
        numbers = [float(x.strip()) for x in numbers_str.split(",") if x.strip()]
        if not numbers:
            return "请提供有效的数字。"
        
        stats = {
            "count": len(numbers),
            "sum": sum(numbers),
            "mean": statistics.mean(numbers),
            "median": statistics.median(numbers),
            "stdev": statistics.stdev(numbers) if len(numbers) > 1 else 0,
            "min": min(numbers),
            "max": max(numbers),
            "range": max(numbers) - min(numbers)
        }
        
        # 计算四分位数
        sorted_nums = sorted(numbers)
        n = len(sorted_nums)
        q1 = sorted_nums[n // 4]
        q3 = sorted_nums[3 * n // 4]
        stats["q1"] = q1
        stats["q3"] = q3
        stats["iqr"] = q3 - q1
        
        return json.dumps(stats, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"计算出错：{str(e)}"


@tool
def detect_anomalies(numbers_str: str, method: str = "iqr") -> str:
    """检测数据中的异常值。
    
    Args:
        numbers_str: 逗号分隔的数字字符串
        method: 检测方法 (iqr/zscore)
    """
    try:
        numbers = [float(x.strip()) for x in numbers_str.split(",") if x.strip()]
        if len(numbers) < 4:
            return "数据点太少，至少需要4个数字。"
        
        anomalies = []
        
        if method == "iqr":
            sorted_nums = sorted(numbers)
            n = len(sorted_nums)
            q1 = sorted_nums[n // 4]
            q3 = sorted_nums[3 * n // 4]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for i, num in enumerate(numbers):
                if num < lower_bound or num > upper_bound:
                    anomalies.append({"index": i, "value": num, "reason": "超出IQR范围"})
        
        elif method == "zscore":
            mean = statistics.mean(numbers)
            stdev = statistics.stdev(numbers)
            if stdev == 0:
                return "所有数值相同，无法检测异常值。"
            
            for i, num in enumerate(numbers):
                z_score = abs((num - mean) / stdev)
                if z_score > 2:
                    anomalies.append({"index": i, "value": num, "z_score": round(z_score, 2)})
        
        if not anomalies:
            return "未检测到异常值。"
        
        return json.dumps({
            "method": method,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"检测出错：{str(e)}"


@tool
def analyze_trend(numbers_str: str, labels_str: str = "") -> str:
    """分析数据趋势（上升、下降、波动）。
    
    Args:
        numbers_str: 逗号分隔的数字字符串
        labels_str: 可选的标签，逗号分隔（如日期、月份）
    """
    try:
        numbers = [float(x.strip()) for x in numbers_str.split(",") if x.strip()]
        labels = [x.strip() for x in labels_str.split(",")] if labels_str else []
        
        if len(numbers) < 2:
            return "至少需要2个数字来分析趋势。"
        
        # 计算变化率
        changes = []
        for i in range(1, len(numbers)):
            change = numbers[i] - numbers[i - 1]
            pct_change = (change / numbers[i - 1] * 100) if numbers[i - 1] != 0 else 0
            changes.append({
                "from": labels[i - 1] if labels else f"点{i - 1}",
                "to": labels[i] if labels else f"点{i}",
                "change": round(change, 2),
                "pct_change": round(pct_change, 2)
            })
        
        # 总体趋势
        overall_change = numbers[-1] - numbers[0]
        overall_pct = (overall_change / numbers[0] * 100) if numbers[0] != 0 else 0
        
        if overall_change > 0:
            trend = "上升"
        elif overall_change < 0:
            trend = "下降"
        else:
            trend = "持平"
        
        # 波动性
        volatility = statistics.stdev(numbers) if len(numbers) > 1 else 0
        
        return json.dumps({
            "overall_trend": trend,
            "overall_change": round(overall_change, 2),
            "overall_pct_change": round(overall_pct, 2),
            "volatility": round(volatility, 2),
            "step_changes": changes
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"趋势分析出错：{str(e)}"


@tool
def compare_datasets(dataset1_str: str, dataset2_str: str, name1: str = "数据集1", name2: str = "数据集2") -> str:
    """比较两组数据集的差异。
    
    Args:
        dataset1_str: 第一组数据，逗号分隔
        dataset2_str: 第二组数据，逗号分隔
        name1: 第一组名称
        name2: 第二组名称
    """
    try:
        ds1 = [float(x.strip()) for x in dataset1_str.split(",") if x.strip()]
        ds2 = [float(x.strip()) for x in dataset2_str.split(",") if x.strip()]
        
        if not ds1 or not ds2:
            return "请提供两组有效的数字。"
        
        comparison = {
            name1: {
                "count": len(ds1),
                "mean": round(statistics.mean(ds1), 2),
                "median": round(statistics.median(ds1), 2),
                "stdev": round(statistics.stdev(ds1), 2) if len(ds1) > 1 else 0
            },
            name2: {
                "count": len(ds2),
                "mean": round(statistics.mean(ds2), 2),
                "median": round(statistics.median(ds2), 2),
                "stdev": round(statistics.stdev(ds2), 2) if len(ds2) > 1 else 0
            },
            "difference": {
                "mean_diff": round(statistics.mean(ds1) - statistics.mean(ds2), 2),
                "median_diff": round(statistics.median(ds1) - statistics.median(ds2), 2)
            }
        }
        
        return json.dumps(comparison, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"比较出错：{str(e)}"


@tool
def generate_data_summary(numbers_str: str, labels_str: str = "") -> str:
    """生成数据摘要报告（包含关键指标和洞察）。"""
    try:
        numbers = [float(x.strip()) for x in numbers_str.split(",") if x.strip()]
        labels = [x.strip() for x in labels_str.split(",")] if labels_str else []
        
        if not numbers:
            return "请提供有效的数字。"
        
        mean = statistics.mean(numbers)
        median = statistics.median(numbers)
        stdev = statistics.stdev(numbers) if len(numbers) > 1 else 0
        
        # 生成洞察
        insights = []
        if mean > median:
            insights.append("数据右偏（均值大于中位数），可能存在较大值拉高平均")
        elif mean < median:
            insights.append("数据左偏（均值小于中位数），可能存在较小值拉低平均")
        else:
            insights.append("数据分布较为对称")
        
        cv = (stdev / mean * 100) if mean != 0 else 0
        if cv > 50:
            insights.append("变异系数较高，数据波动较大")
        elif cv < 10:
            insights.append("变异系数较低，数据较为稳定")
        
        return json.dumps({
            "data_points": len(numbers),
            "labels": labels if labels else None,
            "key_metrics": {
                "mean": round(mean, 2),
                "median": round(median, 2),
                "stdev": round(stdev, 2),
                "min": min(numbers),
                "max": max(numbers),
                "coefficient_of_variation": round(cv, 2)
            },
            "insights": insights
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"生成摘要出错：{str(e)}"


tools = [calculate_statistics, detect_anomalies, analyze_trend, compare_datasets, generate_data_summary]
