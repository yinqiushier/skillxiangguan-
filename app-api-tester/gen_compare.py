#!/usr/bin/env python3
import csv
import sys
import os

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..", "..", "..", "..", "Desktop", "create接口", "app")
if not os.path.exists(WORK_DIR):
    WORK_DIR = "."

def main():
    old_path = os.path.join(WORK_DIR, "test_results_old_api.csv")
    new_path = os.path.join(WORK_DIR, "test_results_new_api.csv")

    if not os.path.exists(old_path) or not os.path.exists(new_path):
        print("错误：找不到结果文件，请先运行 run_compare.py")
        return

    old_results = []
    with open(old_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            old_results.append(row)

    new_results = []
    with open(new_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            new_results.append(row)

    compare_path = os.path.join(WORK_DIR, "test_results_compare.csv")
    with open(compare_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["序号", "用例名称", "旧HTTP", "旧Body", "旧测试结果", "新HTTP", "新Body", "新测试结果", "对比差异"])

        for i in range(min(len(old_results), len(new_results))):
            old_row = old_results[i]
            new_row = new_results[i]

            old_http = old_row[3] if len(old_row) > 3 else ""
            old_body = old_row[4] if len(old_row) > 4 else ""
            old_pass = old_row[6] if len(old_row) > 6 else ""
            new_http = new_row[3] if len(new_row) > 3 else ""
            new_body = new_row[4] if len(new_row) > 4 else ""
            new_pass = new_row[6] if len(new_row) > 6 else ""

            diffs = []
            if old_http != new_http:
                diffs.append(f"HTTP({old_http} vs {new_http})")
            if old_body != new_body:
                diffs.append(f"Body({old_body} vs {new_body})")

            diff = "; ".join(diffs) if diffs else "一致"

            writer.writerow([
                old_row[0] if len(old_row) > 0 else str(i+1),
                old_row[1] if len(old_row) > 1 else "",
                old_http,
                old_body,
                old_pass,
                new_http,
                new_body,
                new_pass,
                diff
            ])

    print(f"Done! 对比结果 saved to {compare_path}")

if __name__ == "__main__":
    main()
