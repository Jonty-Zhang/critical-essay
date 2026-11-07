#!/usr/bin/env python3
"""思辨论文正文的语言检查：查 AI 味、对话痕迹、和稀泥、框架术语外露等。

用法：
    python3 lint_prose.py 论文.md [更多文件 ...]
    python3 lint_prose.py -          # 从标准输入读

只检查正文：跳过代码块、引用块（> 开头）、标题行，以及"参考文献"标题之后的内容。
报告分两级：
    问题  基本可以确定要改
    提示  要看上下文，合理的可以保留
有"问题"级别时退出码为 1，否则为 0。
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

PROBLEM = "问题"
HINT = "提示"


@dataclass
class Rule:
    rid: str
    level: str
    name: str
    pattern: re.Pattern
    advice: str


def r(p: str) -> re.Pattern:
    return re.compile(p)


# ---------- 词句级规则（逐行正则） ----------
RULES: list[Rule] = [
    Rule("dialog", PROBLEM, "对话痕迹",
         r(r"以下是|希望(这|以上|本文)?(对你|对您)?(能)?有(所)?帮助|请告诉我|如需进一步|"
           r"根据(您|你|用户|老师)的要求|根据题目要求|按照(您|你)的要求|好的[，,！!]|当然[！!]"),
         "正文里删掉，交付说明写在正文之外"),
    Rule("placeholder", PROBLEM, "占位符 / 草稿残留",
         r(r"TODO|待补充?|【此处|此处(待|需)|XXX|需核实|\[citation needed\]|（待定）"),
         "补上真实内容，或删掉这句"),
    Rule("ending", PROBLEM, "空洞结尾 / 升华",
         r(r"未来可期|任重道远|值得(我们)?(每个人)?(深思|反思)|让我们(一起|携手)?|意义深远|"
           r"既是挑战(，|也是)?.{0,2}机遇|必将.{0,10}(美好|光明|辉煌)"),
         "删掉，结尾只说论证到了哪一步"),
    Rule("muddle", PROBLEM, "和稀泥",
         r(r"辩证地?(看待|分析|认识)|一分为二|有利有弊|利弊(兼有|并存)|各有千秋|把握好.{0,4}度"),
         "说出在什么条件下哪一方更站得住"),
    Rule("opening", PROBLEM, "时代式套话",
         r(r"随着.{0,12}(社会|时代|科技|技术|经济)?.{0,6}的?(不断|飞速|快速|日益)?(发展|进步|推进)|"
           r"在当今(时代|社会)?|当今社会|自古以来|众所周知"),
         "从具体的分歧、事件、文本写起"),
    Rule("inflate", PROBLEM, "夸大意义",
         r(r"标志着|见证了|彰显了?|具有(重要|深远|重大|里程碑)(的)?(意义|价值)|里程碑|不可磨灭|"
           r"深深植根|奠定了?.{0,6}基础|新篇章|新纪元"),
         "删掉评价，留下事实；要说重要就说清对谁、在哪方面"),
    Rule("promo", PROBLEM, "宣传腔",
         r(r"充满活力|丰富多彩|独特魅力|叹为观止|蓬勃发展|日新月异|方兴未艾|熠熠生辉"),
         "换成具体事实"),
    Rule("ai_words", PROBLEM, "AI 高频词",
         r(r"至关重要|深入探讨|不可或缺|赋能|助力|凸显|全方位|多维度|深度融合|底层逻辑|抓手|闭环|"
           r"值得注意的是|毋庸置疑|显而易见|综上所述|总而言之|不言而喻"),
         "多数可以直接删或换成普通说法"),
    Rule("role", PROBLEM, "回避“是/有”",
         r(r"扮演(着)?.{0,14}角色|发挥(着)?.{0,10}作用|承担(着)?.{0,8}功能"),
         "能说“是”“有”就直接说"),
    Rule("neg_parallel", HINT, "否定式排比",
         r(r"不仅仅是|这不(仅|只)?是.{0,20}[，,]?而是|与其说.{0,20}不如说|不是.{1,15}[，,]而是"),
         "一篇最多一两处；多了改成直接的正面说法"),
    Rule("filler", PROBLEM, "填充短语",
         r(r"在一定程度上|某种程度上|从某种意义上(来说|讲)?|进行了?(深入|全面|系统)的?(分析|研究|探讨)|"
           r"由于.{0,10}的原因|具有.{0,6}的能力"),
         "删掉，或写出具体的程度、意义"),
    Rule("support_vague", HINT, "支撑性泛称",
         r(r"越来越多的人|业界普遍|社会各界|广大(群众|学者)"),
         "换成具体的主体和来源"),
    Rule("absolute", HINT, "全称判断",
         r(r"所有的?|一切|必然|毫无疑问|从来没有|从未|绝对"),
         "确实是全称才保留，否则加范围限定"),
    Rule("framework", HINT, "框架术语外露",
         r(r"图尔敏|论证模型|罗杰斯式|正反合|正题|反题|合题|限定词|反驳环节|保证（warrant）|"
           r"本文采用.{0,12}(模型|结构|框架|方法)进行论证"),
         "正文不出现框架术语，除非课程要求分析论证结构"),
    Rule("three_aspects", HINT, "三段式提示",
         r(r"[三3]个(方面|层面|维度|角度)"),
         "有几项写几项，不必凑三"),
    Rule("triplet", HINT, "三项并列",
         r(r"[一-鿿]{2,4}、[一-鿿]{2,4}(、|和|与|及)[一-鿿]{2,4}(?![、一-鿿]*、)"),
         "确认是真有三项，而不是凑数的形容词"),
    Rule("dash", PROBLEM, "破折号",
         r(r"——|—|--"),
         "换成逗号、冒号、括号，或拆句"),
    Rule("bold", PROBLEM, "正文加粗",
         r(r"\*\*[^*\n]+\*\*|__[^_\n]+__"),
         "论文正文不加粗"),
    Rule("inline_header_list", PROBLEM, "粗体小标题列表",
         r(r"^\s*([-*+]|\d+[.、])\s+\*\*[^*]+(\*\*\s*[：:]|[：:]\s*\*\*)"),
         "改写成段落"),
    Rule("list_item", HINT, "正文列表",
         r(r"^\s*([-*+]\s|\d+[.、]\s?)"),
         "论证段落不要用列表代替；确属并列信息可保留"),
    Rule("en_quote", PROBLEM, "中文里的英文直引号",
         r(r"\"[^\"\n]*[一-鿿][^\"\n]*\""),
         "改用中文引号"),
    Rule("emoji", PROBLEM, "表情符号",
         r("[\U0001F300-\U0001FAFF☀-➿⭐✅❌]"),
         "删掉"),
]

CONNECTOR_START = re.compile(r"^(首先|其次|再次|此外|另外|然而|但是|因此|所以|总之|综上所述|总而言之|最后)[，,]?")
HEDGE = re.compile(r"可能|或许|也许|大概|似乎|在一定程度上|某种程度上|一般来说|往往")
VAGUE_SOURCE = re.compile(r"(有|一些|部分|不少|许多|很多)?(学者|专家|研究者?|调查|报告|数据)(们)?(认为|指出|表明|显示|发现|证实)")
CITATION = re.compile(r"\[\d+(?:[-–,，]\d+)*\]|[（(][^）)]{0,40}\d{4}[a-z]?[^）)]{0,10}[）)]|\^\d+")
SENT_SPLIT = re.compile(r"(?<=[。！？!?])")
HAN = re.compile(r"[一-鿿]")


@dataclass
class Finding:
    file: str
    line: int
    level: str
    name: str
    snippet: str
    advice: str


def body_lines(text: str):
    """产出 (行号, 行文本)，只含正文。"""
    in_code = False
    in_refs = False
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r"^#{1,6}\s", s):
            title = re.sub(r"^#{1,6}\s*", "", s)
            in_refs = bool(re.match(r"^(参考文献|参考资料|References|引用文献)", title))
            continue
        if in_refs and not re.match(r"^(附录|附表|论证蓝图)", s):
            continue
        if s.startswith(">") or not s:
            continue
        if re.fullmatch(r"[-|:\s*_=]+", s):  # 表格分隔行、分割线
            continue
        if re.fullmatch(r"(参考文献|参考资料)[:：]?", s):
            in_refs = True
            continue
        yield i, raw


def snippet_around(line: str, start: int, end: int, pad: int = 12) -> str:
    a = max(0, start - pad)
    b = min(len(line), end + pad)
    return ("…" if a > 0 else "") + line[a:b].strip() + ("…" if b < len(line) else "")


def sentences(line: str) -> list[str]:
    return [x for x in SENT_SPLIT.split(line) if HAN.search(x)]


def lint(name: str, text: str) -> list[Finding]:
    out: list[Finding] = []
    lines = list(body_lines(text))

    for ln, line in lines:
        for rule in RULES:
            for m in rule.pattern.finditer(line):
                out.append(Finding(name, ln, rule.level, rule.name,
                                   snippet_around(line, m.start(), m.end()), rule.advice))

        for s in sentences(line):
            hedges = HEDGE.findall(s)
            if len(hedges) >= 2:
                out.append(Finding(name, ln, PROBLEM, "对冲叠加",
                                   s.strip()[:60], f"一句里有 {len(hedges)} 个对冲词（{'、'.join(hedges)}），最多留一个"))
            if VAGUE_SOURCE.search(s) and not CITATION.search(s):
                m = VAGUE_SOURCE.search(s)
                out.append(Finding(name, ln, PROBLEM, "模糊归因（无引注）",
                                   s.strip()[:60], f"“{m.group(0)}”后面没有引注；补上具体文献，或删掉"))

        sents = [x.strip() for x in sentences(line)]
        for k in range(len(sents) - 2):
            a, b, c = sents[k:k + 3]
            if len(a) >= 2 and a[:2] == b[:2] == c[:2]:
                out.append(Finding(name, ln, HINT, "连续同头排比",
                                   f"{a[:12]}… / {b[:12]}… / {c[:12]}…", "三句同一个开头，像排比，改掉一句"))
            lens = [len(HAN.findall(x)) for x in (a, b, c)]
            if min(lens) >= 12 and max(lens) - min(lens) <= 3:
                out.append(Finding(name, ln, HINT, "句长单调",
                                   f"{a[:12]}…（连续三句约 {lens[0]} 字）", "打断其中一句，长短交错"))

    # 段首连接词：统计
    starts = [(ln, CONNECTOR_START.match(line.strip())) for ln, line in lines]
    starts = [(ln, m.group(1)) for ln, m in starts if m]
    if len(starts) >= 3:
        where = "、".join(f"{ln}行{w}" for ln, w in starts[:8])
        out.append(Finding(name, starts[0][0], PROBLEM, "段首连接词堆砌",
                           where, f"{len(starts)} 段用连接词开头；段间关系靠内容衔接"))

    # 破折号总量
    dash_total = sum(len(re.findall(r"——|—", line)) for _, line in lines)
    if dash_total >= 5:
        out.append(Finding(name, 0, PROBLEM, "破折号总量",
                           f"全文 {dash_total} 处", "压到个位数以内，最好不用"))

    out.sort(key=lambda f: (f.line, f.level != PROBLEM))
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    all_findings: list[Finding] = []
    for path in argv[1:]:
        if path == "-":
            text, name = sys.stdin.read(), "<stdin>"
        else:
            try:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError) as e:
                print(f"读不了 {path}：{e}", file=sys.stderr)
                return 2
            name = path
        all_findings.extend(lint(name, text))

    if not all_findings:
        print("没有发现问题。脚本只查词句和标点，论证本身还要按清单检查。")
        return 0

    n_prob = sum(f.level == PROBLEM for f in all_findings)
    n_hint = len(all_findings) - n_prob
    by_name: dict[str, int] = {}
    for f in all_findings:
        by_name[f.name] = by_name.get(f.name, 0) + 1

    for f in all_findings:
        loc = f"{f.file}:{f.line}" if f.line else f.file
        print(f"[{f.level}] {loc}  {f.name}：{f.snippet}\n        → {f.advice}")
    print()
    print(f"共 {n_prob} 处问题，{n_hint} 处提示。")
    print("按类别：" + "，".join(f"{k} {v}" for k, v in sorted(by_name.items(), key=lambda x: -x[1])))
    return 1 if n_prob else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
