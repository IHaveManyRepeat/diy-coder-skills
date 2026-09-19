# placeholders:
// 示例测试（由 diy-test-framework 渲染）——证明框架能收集并执行；
// 真实用例由 diy-test-author 生成（消费 test-plan.yaml 的 TC）。
describe('脚手架就绪', () => {
  it('断言链路可运行', () => {
    cy.visit('data:text/html,<button aria-label="提交">提交</button>');
    cy.findByRole('button', { name: '提交' }).should('be.visible');
  });
});
