# placeholders:
<?php
// 示例测试（由 diy-test-framework 渲染）——证明 runner 能收集并执行；
// 真实用例由 diy-test-author 生成（消费 test-plan.yaml 的 TC）。
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class ExampleTest extends TestCase
{
    public function testScaffoldIsReady(): void
    {
        $this->assertSame(6, array_sum([1, 2, 3]));
    }
}
