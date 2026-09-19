# placeholders:
# frozen_string_literal: true
# 示例测试（由 diy-test-framework 渲染）——证明 runner 能收集并执行；
# 真实用例由 diy-test-author 生成（消费 test-plan.yaml 的 TC）。
require 'spec_helper'

RSpec.describe '脚手架' do
  it '就绪：断言链路可运行' do
    expect([1, 2, 3].sum).to eq(6)
  end
end
