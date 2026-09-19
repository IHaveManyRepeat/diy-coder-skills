# placeholders: TEST_DIR
<!-- PHPUnit 配置（由 diy-test-framework 渲染；要改请改技能内模板，不要改本文件） -->
<phpunit bootstrap="vendor/autoload.php" colors="true" cacheDirectory=".phpunit.cache">
  <testsuites>
    <testsuite name="default">
      <directory>{{TEST_DIR}}</directory>
    </testsuite>
  </testsuites>
  <source>
    <include>
      <directory>src</directory>
    </include>
  </source>
  <logging>
    <junit outputFile="test-results/junit.xml"/>
  </logging>
</phpunit>
