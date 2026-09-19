# placeholders: CRATE_NAME
// 集成测试示例（由 diy-test-framework 渲染；落 tests/ 目录）——证明 runner 能收集并执行；
// 真实用例由 diy-test-author 生成（消费 test-plan.yaml 的 TC）。
// use {{CRATE_NAME}}::*;

#[test]
fn scaffold_is_ready() {
    let total: i32 = [1, 2, 3].iter().sum();
    assert_eq!(total, 6);
}
