# critical-essay

一个 Claude Code skill，用来写中文大学课程里的思辨性论文：要亮出立场、为立场辩护的那类课程论文、结课论文、评论性作业。

它的做法是先弄清楚争的是什么、对方最强的说法是什么，再挑结构，最后用平实的学术语言写出来。只管内容，不管排版。

## 它会做什么

1. 判断争点。用古典修辞的争点理论，看分歧卡在事实、定义、因果、价值还是对策哪一层。
2. 摆出立场光谱，按 Rapoport 规则把对方立场复述到对方自己会认可的程度。
3. 从下面七种结构里挑 2–3 个给你选，每个都写明为什么适合、代价是什么、章节骨架怎么排。
4. 你选定之后，把每个分论点搭成一个图尔敏单元（主张、理由、依据、保证、限定、反方与回应），再用 Walton 论证型式的关键问题逐个检验。
5. 成文，过论证清单和语言清单，跑检查脚本，交付正文和单独的论证蓝图。

也可以拿一篇现成的初稿进来，只改论证和语言。

## 七种结构

| 结构 | 适合 |
|---|---|
| 古典六部式 | 立场明确、读者中立，争的是事实或定义 |
| 图尔敏全篇式 | 因果、价值、对策题，老师看重推理是否严密 |
| 罗杰斯式 | 伦理、价值冲突大，读者多数持反方 |
| 正反合辩证式 | 两难问题，正反两边都讲得通 |
| 争点递进式 | 问题—对策型论文，按事实、定义、价值、对策层层往上推 |
| 驳立结合式 | 评论某位学者、某本教材或某个流行说法 |
| 比较评估式 | “A 与 B 孰优”，先论证评价标准再逐条比较 |

每种结构的骨架、代价和常见错误写在 [structures.md](critical-essay/references/structures.md)。

## 语言规则

[language.md](critical-essay/references/language.md) 改编自 humanizer-zh（源头是维基百科 WikiProject AI Cleanup 整理的 AI 写作特征），只留下适合课程论文的部分：删套话、删升华句、不用破折号和加粗、核心概念全文一个叫法、“有学者认为”后面必须有引注。幽默、跑题、口语化这几条没有收。另外补了思辨论文特有的几条：不和稀泥，不用“随着……的发展”开头，正文里不出现“图尔敏”“正题”“保证”这类框架术语，不写成平铺直叙的说明文。

AI 写论文还有一个常见毛病：抓住一个次要点（常常是自己推出来的限定条件）反复加码，最后主线淡了。skill 在成文和自检里专门查主次：限定只在反方与回应处展开一次，不许写成“先……才能……”的前提。

## 安装

```bash
git clone https://github.com/Jonty-Zhang/critical-essay ~/.claude/skill-repos/critical-essay
ln -s ~/.claude/skill-repos/critical-essay/critical-essay ~/.claude/skills/critical-essay
```

不能用符号链接的环境（如 Windows），把 `critical-essay` 文件夹直接复制进 `~/.claude/skills/`。脚本只用 Python 标准库，不需要装依赖。

## 使用

在 Claude Code 里输入 `/critical-essay`，后面写上题目、字数、引用要求和材料。也可以直接说“帮我写这篇课程论文，用图尔敏结构”或者“这篇初稿论证太弱，帮我改一下”。

语言检查脚本也可以单独用：

```bash
python3 critical-essay/scripts/lint_prose.py 论文.md      # 有“问题”级别的报告时退出码为 1
cat 草稿.txt | python3 critical-essay/scripts/lint_prose.py -
python3 critical-essay/tests/selftest.py                  # 自测
```

脚本跳过代码块、引用块和“参考文献”之后的内容，只查词句和标点层面的问题。论证本身好不好，要按 [critical-tests.md](critical-essay/references/critical-tests.md) 的清单检查。

## 文件

```
critical-essay/
├── SKILL.md                    主流程
├── references/
│   ├── structures.md           争点判断、结构匹配表、七种结构
│   ├── toulmin-unit.md         分论点怎么搭、怎么写成段落
│   ├── critical-tests.md       论证型式与关键问题、自检清单、改稿诊断
│   └── language.md             学术版去 AI 味规则
├── examples/worked-example.md  一道题从分析走到成文
├── scripts/lint_prose.py       语言检查脚本
└── tests/                      脚本自测与样例
```

## 参考

- Stephen Toulmin, *The Uses of Argument*, 1958
- Wayne C. Booth, Gregory G. Colomb, Joseph M. Williams, *The Craft of Research*
- Richard E. Young, Alton L. Becker, Kenneth L. Pike, *Rhetoric: Discovery and Change*, 1970
- Douglas Walton, *Argumentation Schemes for Presumptive Reasoning*, 1996
- Frans H. van Eemeren, Rob Grootendorst, *A Systematic Theory of Argumentation*, 2004
- Richard Paul, Linda Elder, *The Miniature Guide to Critical Thinking: Concepts and Tools*
- Gerald Graff, Cathy Birkenstein, *They Say / I Say: The Moves That Matter in Academic Writing*
- Daniel C. Dennett, *Intuition Pumps and Other Tools for Thinking*, 2013
- [Purdue OWL: Stasis Theory](https://owl.purdue.edu/owl/general_writing/the_writing_process/stasis_theory/index.html)
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)

## License

MIT
