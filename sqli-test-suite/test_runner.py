#!/usr/bin/env python3
"""
JPAMB SQL Injection Test Runner
Automates execution of all 25 test cases and generates results
"""

import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

class TestRunner:
    def __init__(self, jpamb_path, analyzer_script="my_analyzer.py"):
        self.jpamb_path = Path(jpamb_path)
        self.analyzer_script = analyzer_script
        self.results_dir = self.jpamb_path / "results"
        self.results_dir.mkdir(exist_ok=True)
        
    def load_test_cases(self):
        """Load test case metadata from JSON"""
        test_file = self.jpamb_path / "test_cases.json"
        if not test_file.exists():
            print(f"Error: {test_file} not found")
            print("Run jpamb_setup.py first to generate test cases")
            sys.exit(1)
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        return data['test_cases']
    
    def run_analyzer(self, method_signature):
        """
        Run the analyzer on a single method
        Returns: (outcome, confidence, execution_time)
        """
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, self.analyzer_script, method_signature],
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout per test
                cwd=str(self.jpamb_path)
            )
            
            execution_time = time.time() - start_time
            
            # Parse output (format: "outcome;confidence")
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                # Get first line (main result)
                outcome_line = lines[0]
                
                if ';' in outcome_line:
                    outcome, confidence = outcome_line.split(';', 1)
                    return outcome.strip(), int(confidence), execution_time
                else:
                    return outcome_line.strip(), 0, execution_time
            else:
                # Analyzer failed or returned nothing
                return "error", 0, execution_time
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return "timeout", 0, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"Error running analyzer: {e}")
            return "error", 0, execution_time
    
    def evaluate_result(self, outcome, is_vulnerable_method):
        """
        Evaluate if the analysis result is correct
        
        For vulnerable methods:
            - Should detect SQL injection (outcome contains "injection" or "sql" or "vulnerable")
        For safe methods:
            - Should NOT detect injection (outcome is "ok" or "*")
        """
        outcome_lower = outcome.lower()
        
        # Check if outcome indicates SQL injection
        is_detected = any(keyword in outcome_lower for keyword in 
                         ['injection', 'sql', 'vulnerable', 'sqli', 'taint'])
        
        if is_vulnerable_method:
            # Vulnerable method should be detected
            return is_detected  # True = correct detection
        else:
            # Safe method should NOT be detected
            return not is_detected  # True = correct (no false positive)
    
    def run_all_tests(self):
        """Run all test cases and collect results"""
        test_cases = self.load_test_cases()
        
        print("=" * 70)
        print(f"Running {len(test_cases)} SQL Injection Test Cases")
        print("=" * 70)
        print()
        
        results = []
        total_time = 0
        
        for i, test in enumerate(test_cases, 1):
            print(f"[{i}/{len(test_cases)}] Testing: {test['name']}")
            
            # Test vulnerable method
            print(f"  → Analyzing vulnerable method...", end=" ")
            vuln_outcome, vuln_conf, vuln_time = self.run_analyzer(test['vulnerable_method'])
            vuln_correct = self.evaluate_result(vuln_outcome, is_vulnerable_method=True)
            print(f"{vuln_outcome} ({vuln_time:.2f}s) - {'✓' if vuln_correct else '✗'}")
            
            # Test safe method
            print(f"  → Analyzing safe method...", end=" ")
            safe_outcome, safe_conf, safe_time = self.run_analyzer(test['safe_method'])
            safe_correct = self.evaluate_result(safe_outcome, is_vulnerable_method=False)
            print(f"{safe_outcome} ({safe_time:.2f}s) - {'✓' if safe_correct else '✗'}")
            
            total_time += vuln_time + safe_time
            
            # Store results
            results.append({
                'test_id': test['id'],
                'test_name': test['name'],
                'category': test['category'],
                'vulnerable_method': {
                    'outcome': vuln_outcome,
                    'confidence': vuln_conf,
                    'execution_time': vuln_time,
                    'correct': vuln_correct
                },
                'safe_method': {
                    'outcome': safe_outcome,
                    'confidence': safe_conf,
                    'execution_time': safe_time,
                    'correct': safe_correct
                },
                'passed': vuln_correct and safe_correct
            })
            
            print()
        
        return results, total_time
    
    def calculate_metrics(self, results):
        """Calculate evaluation metrics"""
        total_tests = len(results)
        
        # Detection metrics (vulnerable methods)
        vulnerable_detected = sum(1 for r in results if r['vulnerable_method']['correct'])
        detection_rate = (vulnerable_detected / total_tests) * 100
        
        # False positive metrics (safe methods)
        safe_correct = sum(1 for r in results if r['safe_method']['correct'])
        false_positives = total_tests - safe_correct
        false_positive_rate = (false_positives / total_tests) * 100
        
        # Overall accuracy
        total_correct = sum(1 for r in results if r['passed'])
        accuracy = (total_correct / total_tests) * 100
        
        # Performance metrics
        avg_time_per_test = sum(
            r['vulnerable_method']['execution_time'] + r['safe_method']['execution_time']
            for r in results
        ) / total_tests
        
        # Category breakdown
        categories = {}
        for r in results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0}
            categories[cat]['total'] += 1
            if r['passed']:
                categories[cat]['passed'] += 1
        
        return {
            'total_tests': total_tests,
            'detection_rate': detection_rate,
            'false_positive_rate': false_positive_rate,
            'accuracy': accuracy,
            'avg_time_per_test': avg_time_per_test,
            'categories': categories,
            'vulnerable_detected': vulnerable_detected,
            'false_positives': false_positives,
            'total_passed': total_correct
        }
    
    def print_summary(self, metrics):
        """Print test summary"""
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print()
        
        print(f"Total Test Cases: {metrics['total_tests']}")
        print(f"Tests Passed: {metrics['total_passed']}/{metrics['total_tests']} ({metrics['accuracy']:.1f}%)")
        print()
        
        print("Detection Metrics:")
        print(f"  Detection Rate: {metrics['detection_rate']:.1f}% (Target: 75%+)")
        print(f"  Vulnerable Methods Detected: {metrics['vulnerable_detected']}/{metrics['total_tests']}")
        print()
        
        print("Precision Metrics:")
        print(f"  False Positive Rate: {metrics['false_positive_rate']:.1f}% (Target: <30%)")
        print(f"  False Positives: {metrics['false_positives']}/{metrics['total_tests']}")
        print()
        
        print("Performance:")
        print(f"  Avg Time per Test: {metrics['avg_time_per_test']:.2f}s (Target: <60s)")
        print()
        
        print("Category Breakdown:")
        for cat, stats in metrics['categories'].items():
            pass_rate = (stats['passed'] / stats['total']) * 100
            print(f"  {cat}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")
        print()
        
        # Success criteria evaluation
        print("Success Criteria:")
        detection_ok = metrics['detection_rate'] >= 75
        fp_ok = metrics['false_positive_rate'] < 30
        perf_ok = metrics['avg_time_per_test'] < 60
        
        print(f"  {'✓' if detection_ok else '✗'} Detection Rate ≥75%: {metrics['detection_rate']:.1f}%")
        print(f"  {'✓' if fp_ok else '✗'} False Positive Rate <30%: {metrics['false_positive_rate']:.1f}%")
        print(f"  {'✓' if perf_ok else '✗'} Performance <60s/test: {metrics['avg_time_per_test']:.2f}s")
        print()
        
        overall_pass = detection_ok and fp_ok and perf_ok
        if overall_pass:
            print("Criteria has been met")
        else:
            print("Some criteria has been met")
        print()
    
    def save_results(self, results, metrics):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.results_dir / f"test_results_{timestamp}.json"
        
        output = {
            'timestamp': timestamp,
            'metrics': metrics,
            'test_results': results
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print(f"Results saved to: {result_file}")
        print()
    
    def generate_detailed_report(self, results, metrics):
        """Generate detailed HTML report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"report_{timestamp}.html"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>JPAMB SQLi Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .metric {{ margin: 10px 0; padding: 10px; background: #f0f0f0; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>JPAMB SQL Injection Test Report</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    
    <h2>Summary Metrics</h2>
    <div class="metric">
        <strong>Detection Rate:</strong> {metrics['detection_rate']:.1f}% 
        <span class="{'pass' if metrics['detection_rate'] >= 75 else 'fail'}">
            (Target: 75%+)
        </span>
    </div>
    <div class="metric">
        <strong>False Positive Rate:</strong> {metrics['false_positive_rate']:.1f}%
        <span class="{'pass' if metrics['false_positive_rate'] < 30 else 'fail'}">
            (Target: <30%)
        </span>
    </div>
    <div class="metric">
        <strong>Average Time per Test:</strong> {metrics['avg_time_per_test']:.2f}s
        <span class="{'pass' if metrics['avg_time_per_test'] < 60 else 'fail'}">
            (Target: <60s)
        </span>
    </div>
    
    <h2>Detailed Results</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Test Name</th>
            <th>Category</th>
            <th>Vulnerable Detection</th>
            <th>Safe (No FP)</th>
            <th>Status</th>
        </tr>
"""
        
        for r in results:
            vuln_status = '✓' if r['vulnerable_method']['correct'] else '✗'
            safe_status = '✓' if r['safe_method']['correct'] else '✗'
            overall = 'PASS' if r['passed'] else 'FAIL'
            row_class = 'pass' if r['passed'] else 'fail'
            
            html += f"""        <tr>
            <td>{r['test_id']}</td>
            <td>{r['test_name']}</td>
            <td>{r['category']}</td>
            <td>{vuln_status} {r['vulnerable_method']['outcome']}</td>
            <td>{safe_status} {r['safe_method']['outcome']}</td>
            <td class="{row_class}">{overall}</td>
        </tr>
"""
        
        html += """    </table>
</body>
</html>
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"HTML report saved to: {report_file}")
        print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run JPAMB SQL Injection test suite"
    )
    parser.add_argument(
        "--jpamb-path",
        default="jpamb-sqli",
        help="Path to JPAMB test suite directory"
    )
    parser.add_argument(
        "--analyzer",
        default="my_analyzer.py",
        help="Path to analyzer script"
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Skip HTML report generation"
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = TestRunner(args.jpamb_path, args.analyzer)
    
    # Check if analyzer exists
    if not Path(args.analyzer).exists():
        print(f"Error: Analyzer script not found: {args.analyzer}")
        print("Please provide the path to your analyzer script")
        sys.exit(1)
    
    # Run tests
    results, total_time = runner.run_all_tests()
    
    # Calculate metrics
    metrics = runner.calculate_metrics(results)
    
    # Print summary
    runner.print_summary(metrics)
    
    # Save results
    runner.save_results(results, metrics)
    
    # Generate HTML report
    if not args.no_html:
        runner.generate_detailed_report(results, metrics)
    
    print(f"Total execution time: {total_time:.2f}s")
    print()
    
    # Exit with appropriate code
    if metrics['detection_rate'] >= 75 and metrics['false_positive_rate'] < 30:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failed to meet criteria

if __name__ == "__main__":
    main()
