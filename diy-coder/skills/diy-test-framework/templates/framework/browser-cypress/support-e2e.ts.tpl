// placeholders:
// Cypress support file（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件）
// 每个 spec 之前加载一次。保持最小：全局钩子与自定义命令放这里，别在这里攒共享状态
// （跨用例共享可变状态会破坏确定性隔离，测试代码审计会拦）。

beforeEach(() => {
  // 每条用例从干净状态起跑。需要保留的登录态请走 cy.session()，不要靠上一条用例的残留。
  cy.clearCookies();
  cy.clearLocalStorage();
});
