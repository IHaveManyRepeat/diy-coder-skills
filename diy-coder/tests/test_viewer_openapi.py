# -*- coding: utf-8 -*-
"""diy-viewer openapi 两层渲染契约测试（v4·批4b，2026-10-22）。

断言面（任务书 §5，2026-10-21 已裁准）：
  ① 总览 7 列在场（方法/路径/操作 ID/摘要/功能组/关联需求/请求参数简略）
  ② 分组顺序＝顶层 tags 声明序；未挂 tags/不匹配落「未分组」殿后
  ③ 多 tag 取首个匹配归组（一行一锚）
  ④ 详情竖表关键行在场（方法/路径/操作 ID/摘要/参数/请求体/响应）
  ⑤ 锚 id＝operationId 挂在接口标题；同一 operation 锚唯一
  ⑥ 「操作 ID」列仅一列；总览操作 ID 链接跳详情锚
  ⑦ 无通用渲染 paths 重复节；顶层 tags 通用表跳过
  ⑧ 存量无 tags 产物渲染不丢行（未分组兜底）
  ⑨ 接口级 security 仅与顶层不同时展示
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER_PATH = os.path.join(HERE, "..", "skills", "diy-viewer", "scripts", "viewer.py")
sys.path.insert(0, os.path.dirname(os.path.abspath(VIEWER_PATH)))

NL = chr(10)

# 两层渲染全形态夹具：双功能组＋多 tag＋security 覆盖＋未挂 tags＋tags 不匹配
OPENAPI_DOC = NL.join([
    "openapi: 3.1.0",
    "x-project:",
    "  name: fx",
    "  status: 已定稿",
    "  created: '2026-10-22'",
    "  updated: '2026-10-22'",
    "  revisions: []",
    "info:",
    "  title: 演示契约",
    "  version: 0.1.0",
    "security:",
    "  - cookieAuth: []",
    "tags:",
    "  - name: F-1 认证",
    "  - name: F-2 RBAC",
    "paths:",
    "  /api/login:",
    "    post:",
    "      operationId: login",
    "      summary: 登录",
    "      description: 建立会话",
    "      x-fr: [FR-1.1]",
    "      tags: [F-1 认证]",
    "      parameters:",
    "        - name: returnTo",
    "          in: query",
    "          required: false",
    "          description: 登录后跳转",
    "          schema: {type: string}",
    "      requestBody:",
    "        required: true",
    "        content:",
    "          application/json:",
    "            schema:",
    "              $ref: '#/components/schemas/LoginBody'",
    "      responses:",
    "        '200':",
    "          description: 成功",
    "          headers:",
    "            Set-Cookie:",
    "              description: session 下发",
    "          content:",
    "            application/json:",
    "              schema:",
    "                $ref: '#/components/schemas/LoginResp'",
    "        '401':",
    "          description: 凭据错误",
    "  /api/admin/users:",
    "    get:",
    "      operationId: listUsers",
    "      summary: 列用户",
    "      tags: [F-2 RBAC]",
    "      x-fr: [FR-2.1]",
    "      responses:",
    "        '200':",
    "          description: OK",
    "    post:",
    "      operationId: createUser",
    "      summary: 建用户",
    "      tags: [F-2 RBAC, F-1 认证]",
    "      security: []",
    "      responses:",
    "        '201':",
    "          description: 已建",
    "  /api/legacy:",
    "    get:",
    "      operationId: legacy",
    "      summary: 无标签",
    "      responses:",
    "        '200':",
    "          description: OK",
    "  /api/mystery:",
    "    get:",
    "      operationId: mystery",
    "      summary: 标签不匹配",
    "      tags: [F-9 不存在]",
    "      responses:",
    "        '200':",
    "          description: OK",
    "components:",
    "  securitySchemes:",
    "    cookieAuth:",
    "      type: apiKey",
    "      in: cookie",
    "      name: session",
    "  schemas:",
    "    LoginBody: {type: object}",
    "    LoginResp: {type: object}",
])

# 存量产物形态：无顶层 tags、operation 也无 tags——全部落未分组，不丢行
OPENAPI_STOCK_DOC = NL.join([
    "openapi: 3.1.0",
    "x-project:",
    "  name: fx",
    "  created: '2026-10-22'",
    "  updated: '2026-10-22'",
    "  revisions: []",
    "info:",
    "  title: 存量契约",
    "  version: 0.1.0",
    "security: []",
    "paths:",
    "  /ping:",
    "    get:",
    "      operationId: ping",
    "      summary: 探活",
    "      responses:",
    "        '200':",
    "          description: OK",
    "components:",
    "  securitySchemes: {}",
])


class _Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.out = os.path.join(self.root, "diy-output")
        os.makedirs(self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        with open(os.path.join(self.out, name), "w", encoding="utf-8") as f:
            f.write(content)

    def render(self):
        return subprocess.run(
            [sys.executable, VIEWER_PATH, "--project-root", self.root, "--no-open"],
            capture_output=True, text=True, encoding="utf-8", timeout=60)

    def page(self, name):
        return open(os.path.join(self.out, ".view", name + ".html"),
                    encoding="utf-8").read()


class OpenapiTwoLayerTests(_Fixture):
    def render_openapi(self, doc=OPENAPI_DOC):
        self.write("openapi.yaml", doc)
        p = self.render()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stderr.strip(), "", "渲染诊断非零：%s" % p.stderr)
        return self.page("openapi")

    def test_overview_seven_columns(self):
        """① 总览 7 列在场（含功能组与请求参数简略列）。"""
        html = self.render_openapi()
        self.assertIn('<h2 id="api-overview">接口总览</h2>', html)
        head = re.search(r'id="api-overview".*?</thead>', html, re.S)
        self.assertIsNotNone(head, "总览表头缺失")
        # 表头经 gloss() 可能包 .term span，按文本在场断言（不要求紧贴 </th>）
        for col in ("方法", "路径", "操作 ID", "摘要", "功能组", "关联需求", "请求参数"):
            self.assertIn(">%s" % col, head.group(0), "总览缺列：%s" % col)
        # 请求参数简略格式：名(位置,必填)
        self.assertIn("returnTo(query,选填)", html)

    def test_group_order_and_ungrouped_last(self):
        """② 分组序＝顶层 tags 声明序；未匹配/未挂落未分组殿后。"""
        html = self.render_openapi()
        i1 = html.find("F-1 认证（1 个接口）")
        i2 = html.find("F-2 RBAC（2 个接口）")
        iu = html.find("未分组（2 个接口）")
        self.assertGreater(i1, -1, "F-1 组标题缺失")
        self.assertGreater(i2, i1, "F-2 未排在 F-1 后")
        self.assertGreater(iu, i2, "未分组未殿后")
        # 归组正确：login 在 F-1 块内，legacy/mystery 在未分组块内
        login = html.find('<h4 id="login">')
        legacy = html.find('<h4 id="legacy">')
        mystery = html.find('<h4 id="mystery">')
        self.assertTrue(i1 < login < i2, "login 未落在 F-1 组")
        self.assertTrue(iu < legacy < mystery, "legacy/mystery 未落在未分组")

    def test_multi_tag_first_match_wins(self):
        """③ 多 tag 取首个匹配组名归组（createUser 不落 F-1）。"""
        html = self.render_openapi()
        detail = html[html.find('id="api-detail"'):]
        cu = detail.find('<h4 id="createUser">')
        i2 = detail.find("F-2 RBAC（2 个接口）")
        iu = detail.find("未分组（")
        self.assertGreater(cu, i2, "createUser 未落在 F-2 组")
        self.assertLess(cu, iu)

    def test_detail_vertical_table_key_rows(self):
        """④ 详情竖表关键行在场（字段｜内容两列）。"""
        html = self.render_openapi()
        self.assertIn('<h2 id="api-detail">接口详情</h2>', html)
        login_block = html[html.find('<h4 id="login">'):
                           html.find('<h4 id="listUsers">')]
        for label in ("方法", "路径", "操作 ID", "摘要", "描述", "功能标签",
                      "关联需求", "请求参数", "请求体", "响应定义"):
            self.assertIn(">%s</td>" % label, login_block,
                          "login 详情缺行：%s" % label)
        self.assertIn("Set-Cookie", login_block, "响应头未入详情")
        self.assertIn("#/components/schemas/LoginBody", login_block,
                      "请求体 schema 未入详情")

    def test_anchor_on_title_and_unique(self):
        """⑤ 锚 id＝operationId 挂在接口标题；锚唯一（一 operation 一锚）。"""
        html = self.render_openapi()
        for oid in ("login", "listUsers", "createUser", "legacy", "mystery"):
            self.assertEqual(html.count('id="%s"' % oid), 1, "锚不唯一：%s" % oid)
            self.assertIn('<h4 id="%s">' % oid, html, "锚未挂接口标题：%s" % oid)

    def test_operation_id_single_column_and_links(self):
        """⑥ 「操作 ID」列仅一列；总览行内链接跳详情锚。"""
        html = self.render_openapi()
        overview = html[html.find('id="api-overview"'):html.find('id="api-detail"')]
        self.assertEqual(overview.count(">操作 ID</th>"), 1, "操作 ID 列不止一列")
        self.assertIn('<a href="#login">login</a>', overview,
                      "总览操作 ID 未链到详情锚")
        self.assertNotIn("copy-id", overview, "总览行不应挂复制按钮行锚")

    def test_no_generic_paths_or_tags_section(self):
        """⑦ 通用 paths 树与顶层 tags 表跳过（无三层重复）。"""
        html = self.render_openapi()
        self.assertNotIn('<h2 id="paths">', html, "通用 paths 节未跳过")
        self.assertNotIn('<h2 id="tags">', html, "顶层 tags 通用表未跳过")
        self.assertNotIn(">路径清单</h", html)
        # 其余顶层键保留（components/security/info 通用渲染在场）
        for keep in ('<h2 id="components">', '<h2 id="security">', '<h2 id="info">'):
            self.assertIn(keep, html, "顶层键通用渲染误删：%s" % keep)

    def test_stock_no_tags_renders_ungrouped(self):
        """⑧ 存量无 tags 产物渲染不丢行（未分组兜底）。"""
        html = self.render_openapi(OPENAPI_STOCK_DOC)
        self.assertIn("未分组（1 个接口）", html)
        self.assertIn('<h4 id="ping">', html)
        self.assertIn('<a href="#ping">ping</a>', html)

    def test_security_override_only_when_differs(self):
        """⑨ 接口级 security 仅与顶层不同时展示。"""
        html = self.render_openapi()
        create_block = html[html.find('<h4 id="createUser">'):
                            html.find('<h4 id="legacy">')]
        self.assertIn(">安全要求</td>", create_block, "security 覆盖未展示")
        self.assertIn("显式无鉴权", create_block)
        list_block = html[html.find('<h4 id="listUsers">'):
                          html.find('<h4 id="createUser">')]
        self.assertNotIn(">安全要求</td>", list_block,
                         "security 与顶层一致仍展示")


if __name__ == "__main__":
    unittest.main()
