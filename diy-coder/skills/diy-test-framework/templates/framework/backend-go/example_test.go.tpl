// placeholders: PACKAGE_NAME
// 示例测试（由 diy-test-framework 渲染）——证明 runner 能收集并执行；
// 真实用例由 diy-test-author 生成（消费 test-plan.yaml 的 TC）。
package {{PACKAGE_NAME}}

import "testing"

func TestScaffoldIsReady(t *testing.T) {
	total := 0
	for _, value := range []int{1, 2, 3} {
		total += value
	}
	if total != 6 {
		t.Fatalf("want 6, got %d", total)
	}
}
