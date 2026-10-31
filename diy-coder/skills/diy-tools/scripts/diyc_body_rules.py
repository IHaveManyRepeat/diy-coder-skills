# -*- coding: utf-8 -*-
"""技能正文禁入词表（单源·十模式＋豁免键）。

消费方同引本表、改词只改此处：
- 守卫测试（tests/test_source_anchor_guard.py·安装面增量防线）
- bmb-builder Edit 通道检查脚本（check_body_rules.py·正文门）

本模块自身落在 skills/ 扫描面内——禁入 token 一律以 chr() 码点在运行时
拼装、源文件不含字面（构造避开，非豁免键）。豁免键＝(技能相对路径,
命中原文)，逐条有裁定依据；新增豁免须带依据注记。
"""
import re


def _s(*codepoints):
    """码点串 → 字符串（源文件零字面禁入词，运行时还原）。"""
    return "".join(chr(c) for c in codepoints)


_YUAN, _CE = 0x6E90, 0x4FA7                       # 两字：水原 + 侧面部首
_BAO, _ZHEN, _ZHAO, _BAN = 0x4FDD, 0x771F, 0x7167, 0x642C
_SHOU, _BIAN, _ZI = 0x6536, 0x7F16, 0x81EA        # 收 编 自
_CAI, _DING = 0x88C1, 0x5B9A                      # 裁 定
_DOT = 0x2E                                        # 点

# 十类扩展标记词（顺序无关，逐 pattern 独立命中）
PATTERNS = [
    (_s(_YUAN, _CE), re.compile(_s(_YUAN, _CE))),
    ("trace 批次头", re.compile(r"# trace: B\d")),
    ("batch3-" + "contract", re.compile("batch3-" + "contract")),
    ("拍板引语式" + _s(_CAI, _DING), re.compile(_s(_CAI, _DING) + " ?[0-9]")),
    ("批次号 C\xb7N", re.compile("C\xb7[0-9]")),
    ("census" + "-", re.compile("census" + "-", re.IGNORECASE)),
    (_s(_BAO, _ZHEN, _ZHAO, _BAN), re.compile(_s(_BAO, _ZHEN, _ZHAO, _BAN))),
    (_s(_SHOU, _BIAN, _ZI) + "/" + _s(_CAI, _ZI),
     re.compile(_s(_SHOU, _BIAN, _ZI) + "|" + _s(_CAI, _ZI))),
    # 类①路径锚——排除产品复合词（单一/两/护栏/情报/测试/来/真/数据/散/唯一 等缀）
    (_s(_YUAN) + "+反引号锚", re.compile(
        r"(?<!单一)(?<!两)(?<!护栏)(?<!情报)(?<!测试)(?<!来)(?<!真)(?<!数据)"
        r"(?<!散)(?<!唯一)" + _s(_YUAN) + " `")),
    ("\\" + _s(_DOT) + "analysis/ 目录引用",
     re.compile("\\" + _s(_DOT) + "analysis/")),
]

# 豁免清单：(skills/ 相对路径, 命中原文) —— 逐条有裁定依据
EXEMPT = {
    # 乙-4 用户裁 2026-10-29：bmb-builder 产品行为＝分析报告落点约定
    ("diy-bmb-builder/SKILL.md", _s(_DOT) + "analysis/"),
    ("diy-bmb-builder/steps/03-analyze.md", _s(_DOT) + "analysis/"),
    ("diy-bmb-builder/steps/05-finish.md", _s(_DOT) + "analysis/"),
}
