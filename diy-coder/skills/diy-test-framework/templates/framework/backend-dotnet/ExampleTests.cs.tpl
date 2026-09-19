// placeholders: TEST_PROJECT_NAME
// xUnit 示例测试（由 diy-test-framework 渲染）——证明框架能收集并执行；
// 真实用例由 diy-test-author 生成（消费 test-plan.yaml 的 TC），生成后可由用户裁决移除本示例。
using Xunit;

namespace {{TEST_PROJECT_NAME}};

public sealed class ExampleFixture
{
    public bool Ready => true;

    public int Add(int left, int right) => left + right;
}

public class ExampleTests : IClassFixture<ExampleFixture>
{
    private readonly ExampleFixture _fixture;

    public ExampleTests(ExampleFixture fixture) => _fixture = fixture;

    [Fact]
    public void Scaffold_ready()
    {
        Assert.True(_fixture.Ready);
    }

    [Theory]
    [InlineData(2, 2, 4)]
    [InlineData(2, 3, 5)]
    public void Adds(int left, int right, int expected)
    {
        Assert.Equal(expected, _fixture.Add(left, right));
    }
}
