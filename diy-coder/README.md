# diy-coder

以 YAML 为单一源、HTML 为人类友好投影的 Claude Code 开发工作流技能集，覆盖从 PRD 到循环编码的完整生命周期。

## 安装（D-8）

```bash
# 安装到当前项目（拷贝 skills + 初始化 diy-coder.yaml + 环境冒烟检查）
python install.py <目标项目根>

# 装到本仓库自身（开发期同步）
python install.py
```

- 依赖：Python 3.10+，PyYAML（`pip install pyyaml`；全部脚本以 `python` 直跑）
- `diy-coder.yaml` 是项目级配置（语言/路径/经验库等），仅首次安装创建，重装不覆盖
- `sync.sh` 为兼容壳，等价于 `python install.py`

## 工作流链条

```
diy-help → diy-prd → diy-architecture → diy-openapi（有接口面时）→ diy-design（有前端需求时）
→ diy-epics-stories → diy-test-design → diy-sprint
→ diy-build-loop（被 runner.py 无头驱动：编码→审查→修复 循环至全部任务终态）
  每任务 done 后 runner 自动触发 diy-augment 编码后补测（覆盖率驱动追加 TC 至 test-plan.yaml）

```

- 全部产物为 `diy-output/*.yaml`（单一源），`diy-viewer` 一键渲染成网页审阅，修改永远只改 YAML
- 需求/用例跨文档只引用稳定 ID（FR/AC/TC），viewer 渲染时校验 ID 链并标红悬空/孤儿引用
- 产物写作纪律：主字段白话精简、难懂条目带 `plain`（只写为什么）、过程记录进 `detail`（页面默认折叠）
- `diy-tools` 为内部工具技能（非用户直调），各技能共同的实例解析与跨文档机械核对统一走 `diyc.py`：`python .claude/skills/diy-tools/scripts/diyc.py resolve --json`

## 版权

本项目结构参考 BMAD-METHOD（MIT License）。直接复用其代码的位置保留原始版权声明；命名不使用 BMad/BMAD 商标。
