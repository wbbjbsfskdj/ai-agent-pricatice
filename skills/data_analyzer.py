"""
【文件意义】
企业级数据分析工具 - 为 MCP Agent 提供数据统计、趋势分析、异常检测能力。

在项目中的作用：
1. 使 Agent 能够对用户提供的数据进行统计分析（均值、中位数、标准差、四分位数等）
2. 支持异常值检测（IQR 方法），帮助发现数据中的异常点
3. 支持趋势分析，判断数据是上升、下降还是平稳趋势
4. 支持两个数据集的对比分析，适用于 A/B 测试、同比环比等场景
5. 自动生成数据摘要报告，Agent 可直接向用户展示分析结果
6. 通过 @tool 装饰器注册为 LangChain 工具，Agent 在对话中可自动调用

使用场景示例：
- 用户说："帮我分析一下这组销售数据：100, 150, 200, 180, 250, 300"
- Agent 会调用 calculate_statistics 工具返回统计结果
"""
import json
import statistics
from typing import Optional
from langchain_core.tools import tool

"""
==================== Java 等价实现 ====================

import java.util.*;
import java.util.stream.Collectors;

public class DataAnalyzer {

    // 对应 Python 的 calculate_statistics 函数
    public static String calculateStatistics(String numbersStr) {
        try {
            List<Double> numbers = parseNumbers(numbersStr);
            if (numbers.isEmpty()) {
                return "请提供有效的数字。";
            }

            Map<String, Object> stats = new LinkedHashMap<>();
            stats.put("count", numbers.size());
            stats.put("sum", numbers.stream().mapToDouble(Double::doubleValue).sum());
            stats.put("mean", mean(numbers));
            stats.put("median", median(numbers));
            stats.put("stdev", numbers.size() > 1 ? stdev(numbers) : 0);
            stats.put("min", Collections.min(numbers));
            stats.put("max", Collections.max(numbers));
            stats.put("range", Collections.max(numbers) - Collections.min(numbers));

            // 计算四分位数
            List<Double> sorted = new ArrayList<>(numbers);
            Collections.sort(sorted);
            int n = sorted.size();
            double q1 = sorted.get(n / 4);
            double q3 = sorted.get(3 * n / 4);
            stats.put("q1", q1);
            stats.put("q3", q3);
            stats.put("iqr", q3 - q1);

            return toJson(stats);
        } catch (Exception e) {
            return "计算出错：" + e.getMessage();
        }
    }

    // 对应 Python 的 detect_anomalies 函数
    public static String detectAnomalies(String numbersStr, String method) {
        try {
            List<Double> numbers = parseNumbers(numbersStr);
            if (numbers.size() < 4) {
                return "数据点太少，至少需要4个数字。";
            }

            List<Map<String, Object>> anomalies = new ArrayList<>();

            if ("iqr".equals(method)) {
                List<Double> sorted = new ArrayList<>(numbers);
                Collections.sort(sorted);
                int n = sorted.size();
                double q1 = sorted.get(n / 4);
                double q3 = sorted.get(3 * n / 4);
                double iqr = q3 - q1;
                double lowerBound = q1 - 1.5 * iqr;
                double upperBound = q3 + 1.5 * iqr;

                for (int i = 0; i < numbers.size(); i++) {
                    double num = numbers.get(i);
                    if (num < lowerBound || num > upperBound) {
                        Map<String, Object> anomaly = new LinkedHashMap<>();
                        anomaly.put("index", i);
                        anomaly.put("value", num);
                        anomaly.put("reason", "超出IQR范围");
                        anomalies.add(anomaly);
                    }
                }
            } else if ("zscore".equals(method)) {
                double mean = mean(numbers);
                double stdev = stdev(numbers);
                if (stdev == 0) {
                    return "所有数值相同，无法检测异常值。";
                }

                for (int i = 0; i < numbers.size(); i++) {
                    double num = numbers.get(i);
                    double zScore = Math.abs((num - mean) / stdev);
                    if (zScore > 2) {
                        Map<String, Object> anomaly = new LinkedHashMap<>();
                        anomaly.put("index", i);
                        anomaly.put("value", num);
                        anomaly.put("z_score", Math.round(zScore * 100.0) / 100.0);
                        anomalies.add(anomaly);
                    }
                }
            }

            if (anomalies.isEmpty()) {
                return "未检测到异常值。";
            }

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("method", method);
            result.put("anomaly_count", anomalies.size());
            result.put("anomalies", anomalies);
            return toJson(result);
        } catch (Exception e) {
            return "检测出错：" + e.getMessage();
        }
    }

    // 对应 Python 的 analyze_trend 函数
    public static String analyzeTrend(String numbersStr, String labelsStr) {
        try {
            List<Double> numbers = parseNumbers(numbersStr);
            List<String> labels = labelsStr != null && !labelsStr.isEmpty()
                    ? Arrays.stream(labelsStr.split(",")).map(String::trim).collect(Collectors.toList())
                    : Collections.emptyList();

            if (numbers.size() < 2) {
                return "至少需要2个数字来分析趋势。";
            }

            // 计算变化率
            List<Map<String, Object>> changes = new ArrayList<>();
            for (int i = 1; i < numbers.size(); i++) {
                double change = numbers.get(i) - numbers.get(i - 1);
                double pctChange = numbers.get(i - 1) != 0 ? (change / numbers.get(i - 1) * 100) : 0;

                Map<String, Object> stepChange = new LinkedHashMap<>();
                stepChange.put("from", !labels.isEmpty() ? labels.get(i - 1) : "点" + (i - 1));
                stepChange.put("to", !labels.isEmpty() ? labels.get(i) : "点" + i);
                stepChange.put("change", Math.round(change * 100.0) / 100.0);
                stepChange.put("pct_change", Math.round(pctChange * 100.0) / 100.0);
                changes.add(stepChange);
            }

            // 总体趋势
            double overallChange = numbers.get(numbers.size() - 1) - numbers.get(0);
            double overallPct = numbers.get(0) != 0 ? (overallChange / numbers.get(0) * 100) : 0;

            String trend;
            if (overallChange > 0) trend = "上升";
            else if (overallChange < 0) trend = "下降";
            else trend = "持平";

            double volatility = numbers.size() > 1 ? stdev(numbers) : 0;

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("overall_trend", trend);
            result.put("overall_change", Math.round(overallChange * 100.0) / 100.0);
            result.put("overall_pct_change", Math.round(overallPct * 100.0) / 100.0);
            result.put("volatility", Math.round(volatility * 100.0) / 100.0);
            result.put("step_changes", changes);
            return toJson(result);
        } catch (Exception e) {
            return "趋势分析出错：" + e.getMessage();
        }
    }

    // 对应 Python 的 compare_datasets 函数
    public static String compareDatasets(String ds1Str, String ds2Str, String name1, String name2) {
        try {
            List<Double> ds1 = parseNumbers(ds1Str);
            List<Double> ds2 = parseNumbers(ds2Str);

            if (ds1.isEmpty() || ds2.isEmpty()) {
                return "请提供两组有效的数字。";
            }

            Map<String, Object> comparison = new LinkedHashMap<>();

            Map<String, Object> stats1 = new LinkedHashMap<>();
            stats1.put("count", ds1.size());
            stats1.put("mean", Math.round(mean(ds1) * 100.0) / 100.0);
            stats1.put("median", Math.round(median(ds1) * 100.0) / 100.0);
            stats1.put("stdev", ds1.size() > 1 ? Math.round(stdev(ds1) * 100.0) / 100.0 : 0);

            Map<String, Object> stats2 = new LinkedHashMap<>();
            stats2.put("count", ds2.size());
            stats2.put("mean", Math.round(mean(ds2) * 100.0) / 100.0);
            stats2.put("median", Math.round(median(ds2) * 100.0) / 100.0);
            stats2.put("stdev", ds2.size() > 1 ? Math.round(stdev(ds2) * 100.0) / 100.0 : 0);

            Map<String, Object> diff = new LinkedHashMap<>();
            diff.put("mean_diff", Math.round((mean(ds1) - mean(ds2)) * 100.0) / 100.0);
            diff.put("median_diff", Math.round((median(ds1) - median(ds2)) * 100.0) / 100.0);

            comparison.put(name1, stats1);
            comparison.put(name2, stats2);
            comparison.put("difference", diff);
            return toJson(comparison);
        } catch (Exception e) {
            return "比较出错：" + e.getMessage();
        }
    }

    // 对应 Python 的 generate_data_summary 函数
    public static String generateDataSummary(String numbersStr, String labelsStr) {
        try {
            List<Double> numbers = parseNumbers(numbersStr);
            List<String> labels = labelsStr != null && !labelsStr.isEmpty()
                    ? Arrays.stream(labelsStr.split(",")).map(String::trim).collect(Collectors.toList())
                    : Collections.emptyList();

            if (numbers.isEmpty()) {
                return "请提供有效的数字。";
            }

            double mean = mean(numbers);
            double median = median(numbers);
            double stdev = numbers.size() > 1 ? stdev(numbers) : 0;

            // 生成洞察
            List<String> insights = new ArrayList<>();
            if (mean > median) {
                insights.add("数据右偏（均值大于中位数），可能存在较大值拉高平均");
            } else if (mean < median) {
                insights.add("数据左偏（均值小于中位数），可能存在较小值拉低平均");
            } else {
                insights.add("数据分布较为对称");
            }

            double cv = mean != 0 ? (stdev / mean * 100) : 0;
            if (cv > 50) {
                insights.add("变异系数较高，数据波动较大");
            } else if (cv < 10) {
                insights.add("变异系数较低，数据较为稳定");
            }

            Map<String, Object> keyMetrics = new LinkedHashMap<>();
            keyMetrics.put("mean", Math.round(mean * 100.0) / 100.0);
            keyMetrics.put("median", Math.round(median * 100.0) / 100.0);
            keyMetrics.put("stdev", Math.round(stdev * 100.0) / 100.0);
            keyMetrics.put("min", Collections.min(numbers));
            keyMetrics.put("max", Collections.max(numbers));
            keyMetrics.put("coefficient_of_variation", Math.round(cv * 100.0) / 100.0);

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("data_points", numbers.size());
            result.put("labels", labels.isEmpty() ? null : labels);
            result.put("key_metrics", keyMetrics);
            result.put("insights", insights);
            return toJson(result);
        } catch (Exception e) {
            return "生成摘要出错：" + e.getMessage();
        }
    }

    // ========== 辅助方法 ==========

    private static List<Double> parseNumbers(String input) {
        return Arrays.stream(input.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Double::parseDouble)
                .collect(Collectors.toList());
    }

    private static double mean(List<Double> numbers) {
        return numbers.stream().mapToDouble(Double::doubleValue).average().orElse(0);
    }

    private static double median(List<Double> numbers) {
        List<Double> sorted = new ArrayList<>(numbers);
        Collections.sort(sorted);
        int n = sorted.size();
        if (n % 2 == 0) {
            return (sorted.get(n / 2 - 1) + sorted.get(n / 2)) / 2.0;
        }
        return sorted.get(n / 2);
    }

    private static double stdev(List<Double> numbers) {
        double mean = mean(numbers);
        double variance = numbers.stream()
                .mapToDouble(x -> Math.pow(x - mean, 2))
                .sum() / (numbers.size() - 1);
        return Math.sqrt(variance);
    }

    private static String toJson(Map<?, ?> map) {
        // 实际项目中使用 Jackson/Gson
        return "";
    }
}

======================================================
"""


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
