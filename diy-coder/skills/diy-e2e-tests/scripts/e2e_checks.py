# -*- coding: utf-8 -*-
"""diy-e2e-tests checks 域：TC 校验常量与用例载入/校验/diyc 交叉核对（record 的校验面）。."""

import io
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "diy-tools", "scripts"))
from diyc_lib import display_path, load_yaml_safe, nonempty, v  # noqa: E402

PLAN_FILE = "test-plan.yaml"
STORIES_FILE = "stories.yaml"

E2E_TYPE = "端到端"
E2E_TECHNIQUE = "场景"              # diy-test-design Schema：九技法在册值，端到端用户旅程
RECORD_STATUSES = ("通过", "失败")  # 实测结果：本技能只记已跑过的用例
PRIORITIES = ("P0", "P1", "P2")
DIMENSIONS = ("正向", "边界", "异常", "安全", "性能")  # diy-test-design Schema：五轴·一条用例一个轴
TC_RE = re.compile(r"TC-\d+(?:\.\d+)+")
AC_RE = re.compile(r"AC-\d+(?:\.\d+)+")
FH_RE = re.compile(r"FH-\d+(?:\.\d+){2}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# ---------------------------------------------------------------- record

def load_tc_cases(path, show):
    """读 TC JSON 文件 → (cases | None, violations)。形态：[...] 或 {"test_cases": [...]}。"""
    if not os.path.isfile(path):
        return None, [v("MISSING_FILE", show, "TC 文件不存在（先落本次生成的用例 JSON）")]
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as e:
        return None, [v("ENTRY_INVALID", show, "TC 文件不是合法 JSON：%s" % e)]
    except OSError as e:
        return None, [v("MISSING_FILE", show, "TC 文件不可读：%s" % e)]
    if isinstance(data, dict):
        data = data.get("test_cases")
    if not isinstance(data, list) or not data:
        return None, [v("ENTRY_INVALID", show,
                        "TC 文件须为用例数组（或 {\"test_cases\": [...]}）且非空")]
    return data, []

def ac_of(tc_id):
    """TC-5.1.2 → AC-5.1（id 的 AC 前缀，须与 ac 字段一致）。"""
    return "AC-" + str(tc_id)[len("TC-"):].rsplit(".", 1)[0]

def req(violations, where, value, label):
    if not nonempty(value):
        violations.append(v("EMPTY_FIELD", where, "%s 缺失或为空" % label))
        return False
    return True

def enum(violations, where, value, allowed, label):
    if not nonempty(value):
        violations.append(v("EMPTY_FIELD", where, "%s 缺失或为空" % label))
        return False
    if str(value) not in allowed:
        violations.append(v("ENUM_INVALID", where, "%s 越界：%s（合法集 %s）"
                            % (label, value, "|".join(allowed))))
        return False
    return True

def check_case(case, index, show, known_ids, seen_new, known_acs, stories_available,
               known_fh=None):
    known_fh = known_fh if known_fh is not None else set()
    """单条 TC 校验；where 相对 project-root、正斜杠。"""
    where = "%s test_cases[%d]" % (show, index)
    violations = []
    if not isinstance(case, dict):
        return [v("ENTRY_INVALID", where, "用例不是映射")]

    tc_id = case.get("id")
    where_id = "%s.id" % where
    if req(violations, where_id, tc_id, "id"):
        tc_id = str(tc_id)
        if not TC_RE.fullmatch(tc_id):
            violations.append(v("ENUM_INVALID", where_id,
                                "id 须为 TC-{ac}.{seq}（如 TC-5.1.2），实为 %s" % tc_id))
        elif tc_id in seen_new or tc_id in known_ids:
            violations.append(v("DUPLICATE_ID", where_id,
                                "TC ID %s 已存在（续号不重号：取该 AC 现有最大序号 + 1）"
                                % tc_id))

    ac = case.get("ac")
    where_ac = "%s.ac" % where
    if not nonempty(ac):
        violations.append(v("EMPTY_FIELD", where_ac,
                            "ac 缺失或为空（每个用例须绑定一个现有 AC ID）"))
    elif not isinstance(ac, str):
        violations.append(v("ENTRY_INVALID", where_ac,
                            "ac 须为单个 AC ID 字符串（e2e 用例一条绑一个 AC）"))
    elif not AC_RE.fullmatch(ac):
        violations.append(v("ENUM_INVALID", where_ac, "ac 须为 AC-x.y 形态，实为 %s" % ac))
    elif nonempty(tc_id) and TC_RE.fullmatch(str(tc_id)) and ac_of(tc_id) != ac:
        violations.append(v("ENTRY_INVALID", where_id,
                            "id 的 AC 前缀须与 ac 一致：%s 对应 %s，实为 %s"
                            % (tc_id, ac_of(tc_id), ac)))
    elif stories_available and ac not in known_acs:
        violations.append(v("UNKNOWN_ID", where_ac, "%s 在 %s 中不存在" % (ac, STORIES_FILE)))

    req(violations, "%s.title" % where, case.get("title"), "title")
    enum(violations, "%s.type" % where, case.get("type"), (E2E_TYPE,), "type")
    enum(violations, "%s.priority" % where, case.get("priority"), PRIORITIES, "priority")
    enum(violations, "%s.technique" % where, case.get("technique"),
         (E2E_TECHNIQUE,), "technique")
    enum(violations, "%s.dimension" % where, case.get("dimension"),
         DIMENSIONS, "dimension（五轴）")
    kt = case.get("kill_target")
    if req(violations, "%s.kill_target" % where, kt, "kill_target（引用 FH ID）"):
        refs = kt if isinstance(kt, list) else [kt]
        for j, ref in enumerate(refs):
            if isinstance(ref, str) and FH_RE.fullmatch(ref) and ref not in known_fh:
                fh = case.get("fault_hypothesis")
                if not (isinstance(fh, dict) and fh.get("id") == ref):
                    violations.append(v(
                        "UNKNOWN_ID",
                        "%s.kill_target[%d]" % (where, j)
                        if isinstance(kt, list) else "%s.kill_target" % where,
                        "%s 不在既有 FH 中——新故障先落 FH：同条目带 "
                        "fault_hypothesis: {id: %s, ac, text}（id 与 kill_target 一致）"
                        % (ref, ref)))
    fh = case.get("fault_hypothesis")
    if fh is not None:
        fhw = "%s.fault_hypothesis" % where
        if not isinstance(fh, dict):
            violations.append(v("ENTRY_INVALID", fhw,
                                "fault_hypothesis 须为映射 {id, ac, text}"))
        else:
            req(violations, fhw + ".id", fh.get("id"), "FH id")
            req(violations, fhw + ".ac", fh.get("ac"), "FH ac")
            req(violations, fhw + ".text", fh.get("text"), "FH text")
            if isinstance(fh.get("id"), str) and not FH_RE.fullmatch(fh["id"]):
                violations.append(v("ENUM_INVALID", fhw + ".id",
                                    "FH id 须为 FH-x.y.z 形态，实为 %s" % fh["id"]))
            fh_ac, tc_ac = fh.get("ac"), case.get("ac")
            if isinstance(fh_ac, str) and isinstance(tc_ac, str) and fh_ac != tc_ac:
                violations.append(v("ENUM_INVALID", fhw + ".ac",
                                    "fault_hypothesis.ac 须与用例 ac 一致：%s vs %s"
                                    % (fh_ac, tc_ac)))
    api_refs = case.get("api_refs")
    if api_refs is not None:
        if not (isinstance(api_refs, list) and api_refs):
            violations.append(v("EMPTY_FIELD", "%s.api_refs" % where,
                                "api_refs 形状异常（非空列表；缺席即整键省略）"))
        else:
            for j, anchor in enumerate(api_refs):
                if not (isinstance(anchor, dict)
                        and all(isinstance(anchor.get(k), str) and anchor.get(k).strip()
                                for k in ("operationId", "path", "method"))):
                    violations.append(v("EMPTY_FIELD", "%s.api_refs[%d]" % (where, j),
                                        "复合锚形状异常（须含 operationId/path/method 三键）"))
    enum(violations, "%s.status" % where, case.get("status"), RECORD_STATUSES, "status")
    steps = case.get("steps")
    if not (isinstance(steps, list) and any(nonempty(x) for x in steps)):
        violations.append(v("EMPTY_FIELD", "%s.steps" % where,
                            "steps 缺失或为空（用例须可执行：具体步骤 + 预期结果）"))
    return violations

def load_known(output_dir, show, violations, warnings):
    """既有 test-plan.yaml → (plan, 既有 TC id 集, 故事 AC 集)。缺失 → 违规（零产出）。"""
    plan, err = load_yaml_safe(os.path.join(output_dir, PLAN_FILE))
    if plan is None and err is None:
        violations.append(v("MISSING_FILE", show,
                            "%s 不存在（用例须追加进既有测试计划——先跑 diy-test-design）"
                            % PLAN_FILE))
        return None, set(), set(), False
    if err is not None:
        violations.append(v("UNPARSABLE_YAML", show, "YAML 解析失败：%s" % err))
        return None, set(), set(), False
    if not isinstance(plan, dict):
        violations.append(v("EMPTY_FIELD", show, "顶层不是映射（须为 project + test_cases）"))
        return None, set(), set(), False
    cases = plan.get("test_cases")
    if not isinstance(cases, list):
        violations.append(v("EMPTY_FIELD", show + " test_cases",
                            "test_cases 缺失或不是列表（追加目标不存在）"))
        return None, set(), set(), False
    known_ids = {str(c["id"]) for c in cases
                 if isinstance(c, dict) and nonempty(c.get("id"))}

    stories, s_err = load_yaml_safe(os.path.join(output_dir, STORIES_FILE))
    known_acs = set()
    stories_available = False
    if s_err is not None:
        warnings.append(v("UNPARSABLE_YAML", STORIES_FILE,
                          "上游文档不可解析，ac 引用无法核验：%s" % s_err))
    elif stories is None:
        warnings.append(v("MISSING_FILE", STORIES_FILE,
                          "stories.yaml 缺席：ac 引用无法核验（追加仍放行，由 diyc 复查）"))
    else:
        stories_available = True
        items = stories.get("stories") if isinstance(stories, dict) else None
        for story in items if isinstance(items, list) else []:
            if not isinstance(story, dict):
                continue
            acs = story.get("acceptance_criteria")
            for ac in acs if isinstance(acs, list) else []:
                if isinstance(ac, dict) and nonempty(ac.get("id")):
                    known_acs.add(str(ac["id"]))
    return plan, known_ids, known_acs, stories_available

def diyc_check_test_plan(script, project_root, output_dir):
    """委派 diyc check --type test-plan（§2.3 跨文档核对唯一入口）。

    返回 (block, warnings)：违规并入 block.check.violations（warning 面），不阻塞 exit。
    """
    warnings = []
    block = {"available": False, "script": None, "check": {"ok": None, "violations": [],
                                                           "counts": {}}}
    if not os.path.isfile(script):
        warnings.append(v("TOOL_MISSING", "diy-tools/scripts/diyc.py",
                          "diyc.py 缺席：追加后全链交叉核对降级，请会话侧人工复核"))
        return block, warnings
    block["available"] = True
    block["script"] = display_path(script, project_root)
    cmd = [sys.executable, script, "check", "--type", "test-plan",
           "--project-root", project_root, "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except OSError as e:
        warnings.append(v("TOOL_ERROR", "diyc.py check --type test-plan",
                          "diyc 子进程无法启动：%s" % e))
        return block, warnings
    if proc.returncode not in (0, 1):
        tail = " ".join((proc.stderr or proc.stdout or "").split())[-200:]
        warnings.append(v("TOOL_ERROR", "diyc.py check --type test-plan",
                          "diyc 非预期退出码 %s（期望 0|1）：%s"
                          % (proc.returncode, tail or "无输出")))
        return block, warnings
    payload = None
    for line in reversed((proc.stdout or "").splitlines()):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            break
        except ValueError:
            continue
    if not isinstance(payload, dict):
        warnings.append(v("TOOL_ERROR", "diyc.py check --type test-plan",
                          "diyc 回执不可解析（--json 面单行 JSON 缺失）"))
        return block, warnings
    # diyc 自解析产物目录：与本引擎 --output-dir 不一致时证据来自另一目录，须显式告警
    resolved = payload.get("output_dir")
    if nonempty(resolved):
        a = os.path.normcase(os.path.abspath(os.path.join(project_root, str(resolved))))
        if a != os.path.normcase(os.path.abspath(output_dir)):
            warnings.append(v("SET_MISMATCH", str(resolved),
                              "diyc 解析的产物目录与本引擎 --output-dir 不一致："
                              "交叉核对证据可能来自另一目录"))
    block["check"] = {"ok": payload.get("ok"),
                      "violations": [x for x in payload.get("violations") or []
                                     if isinstance(x, dict)],
                      "counts": payload.get("counts") if isinstance(
                          payload.get("counts"), dict) else {}}
    return block, warnings
