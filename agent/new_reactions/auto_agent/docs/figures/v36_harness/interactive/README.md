# V3.6 交互流程图（导师要求，2026-11-17）

导师要求：流程图要能点开某个节点，里面有 **工具细则、功能解释、case example**；节点折叠或整体缩小时，只显示 high-level pipeline（与 `../V36_lanes.png` 同一张三泳道图）。

- 源文件：`V36_interactive.html`（单文件，无依赖）
- 在线版（私有，分享需在页面 Share 菜单里加人）：https://claude.ai/artifact/YXzzURRnhV8wDTH6rST5kR
- 内容来源：`docs/V36_HYBRID_HARNESS.md`、`docs/UO2_LIBRARY.md`、实例取自 `D:\agent_runs\ch4_v36_t14` 和 `evaluation/ch4_v36_test/ch4_builds.json`。

## 给继续改流程的会话

流程每改一次（新节点、新工具、新一轮运行结果），同步改这个页面：

1. 节点数据都在 HTML 末尾的 `const N = [...]`：`tools`（工具细则）、`what`（功能解释）、`ex`（实例）。新节点加一项并给 `x,y` 坐标；连线在 `<svg class="wires">` 里。
2. 实例换成最新一次有效运行，标明运行名。
3. 改完用 Artifact 工具带上面的 URL 发布到同一链接（先 `action: read` 该 URL 再发布），不要新开链接。
4. 同时更新静态图 `../make_v36_lanes.py`，两张图的主流程保持一致。
