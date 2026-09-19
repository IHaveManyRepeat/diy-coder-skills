// placeholders: TEST_PACKAGE
// 示例测试（由 diy-test-framework 渲染）——证明构建链能收集并执行；
// 真实用例由 diy-test-author 生成（消费 test-plan.yaml 的 TC）。
package {{TEST_PACKAGE}};

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class ExampleTest {

    @Test
    void scaffoldIsReady() {
        assertEquals(6, java.util.List.of(1, 2, 3).stream().mapToInt(Integer::intValue).sum());
    }
}
