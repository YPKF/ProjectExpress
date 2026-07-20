"""Report generation helper (Python side of the hybrid worker)."""
import os
import subprocess


def render_report(report_name):
    # VULN: shell=True with user input (OS command injection)
    subprocess.run("cat reports/" + report_name, shell=True)


def compute_metric(expr):
    # VULN: eval on user-supplied expression (code injection)
    return eval(expr)


API_KEY = "sk-live-9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c"  # VULN: hardcoded secret
