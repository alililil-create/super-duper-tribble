"""真实执行全部程序，保存标准输出、错误和退出码。"""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def main():
    logs = ROOT / "runs"
    logs.mkdir(exist_ok=True)
    failed = []
    scripts = sorted((ROOT / "examples").glob("[0-9][0-9]_*.py"))
    for script in scripts:
        if int(script.name[:2]) >= 10:
            continue
        print(f"\n> python examples/{script.name}", flush=True)
        result = subprocess.run([sys.executable, "-u", str(script)], cwd=ROOT,
                                env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                                capture_output=True, text=True, encoding="utf-8", timeout=300)
        output = result.stdout + result.stderr
        print(output, end="", flush=True)
        print(f"[退出码：{result.returncode}]")
        (logs / (script.stem + ".txt")).write_text(output + f"\n退出码：{result.returncode}\n", encoding="utf-8")
        if result.returncode:
            failed.append(script.name)
    if failed:
        raise SystemExit("运行失败：" + ", ".join(failed))
    subprocess.run([sys.executable, str(ROOT / 'run_advanced.py')], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / 'run_project.py')], cwd=ROOT, check=True)
    print(f"\n全部 {len(scripts)+6} 项模块运行成功。")

if __name__ == "__main__":
    main()
