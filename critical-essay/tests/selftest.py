#!/usr/bin/env python3
"""lint_prose.py 的自测：坏样例要报出预期的问题，好样例不能有"问题"级别的报告。

用法：python3 tests/selftest.py
"""

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("lint_prose", HERE.parent / "scripts" / "lint_prose.py")
lp = importlib.util.module_from_spec(spec)
sys.modules["lint_prose"] = lp
spec.loader.exec_module(lp)

EXPECT_IN_BAD = {
    "对话痕迹", "占位符 / 草稿残留", "空洞结尾 / 升华", "和稀泥", "时代式套话",
    "夸大意义", "AI 高频词", "回避“是/有”", "否定式排比", "填充短语", "对冲叠加",
    "模糊归因（无引注）", "段首连接词堆砌", "破折号", "正文加粗", "粗体小标题列表",
    "表情符号", "框架术语外露",
}

failures = []

bad = lp.lint("bad", (HERE / "bad_sample.md").read_text(encoding="utf-8"))
got = {f.name for f in bad}
missing = EXPECT_IN_BAD - got
if missing:
    failures.append(f"坏样例漏报：{sorted(missing)}")

good = lp.lint("good", (HERE / "good_sample.md").read_text(encoding="utf-8"))
false_pos = [f for f in good if f.level == lp.PROBLEM]
if false_pos:
    failures.append("好样例误报：" + "；".join(f"{f.line}行 {f.name}：{f.snippet}" for f in false_pos))

# 带引注的归因不应报"模糊归因"
cited = lp.lint("cited", "王某（2021）的研究表明，样本中七成学生每天使用。\n有研究指出[3]，这一比例在下降。\n")
if any(f.name == "模糊归因（无引注）" for f in cited):
    failures.append("带引注的句子被误报为模糊归因")

# 参考文献、代码块、引用块不检查
skipped = lp.lint("skip", "正文一句。\n\n> 引文里的综上所述不该报。\n\n```\n至关重要\n```\n\n## 参考文献\n\n[1] 某某. 赋能与至关重要[J]. 2020.\n")
if skipped:
    failures.append("跳过区域被检查了：" + "；".join(f.name for f in skipped))

if failures:
    print("自测失败：")
    for x in failures:
        print(" -", x)
    sys.exit(1)
print(f"自测通过：坏样例报出 {len(got)} 类问题（预期的 {len(EXPECT_IN_BAD)} 类都在），好样例 0 处问题，引注与跳过区域判断正确。")
