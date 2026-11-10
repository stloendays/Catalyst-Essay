# 三个新反应的论文下载

清单由 AI 生成：先在 OpenAlex 按标题检索（不限开放获取），再由 gpt-5.6（API-YES）读标题和摘要做两件事：判断是不是本反应的实验论文；判断摘要里报告进料条件、转化率、选择性和流量/空速的可能性高不高。按"数据可能性 → 置信度 → 引用数"排序，每个反应取前 15 篇。

| 文件 | 内容 |
|---|---|
| `nh3dec_dois.txt` | 氨分解 15 篇 |
| `rwgs_dois.txt` | 逆水煤气变换 15 篇 |
| `etoh_dois.txt` | 乙醇脱水制乙烯 15 篇 |
| `<反应>_candidates.csv` | 检索到的全部候选与筛选理由（用于报"筛了多少、下载了多少、可用多少"） |

## 怎么下载

在 PowerShell 里运行一条命令：

```powershell
& "D:\论文-AI4S\wt-newrxn\agent\new_reactions\downloads\run_downloads.ps1"
```

它对每个反应依次做三件事：

1. 检查 NUS 登录，过期了会自动打开登录页，你在手机上确认 MFA。
2. 自动下载：开放获取和学校代理能直接拿到的，不弹窗。
3. 还缺的论文进入 assist：nus-fetch 自己的 Chrome 窗口逐篇打开，遇到人机验证时窗口会跳到前面，你只需要完成验证，找 PDF、核对 DOI、存档都是自动的。

最后打印每个反应下到了几篇、还缺哪些（`<反应>_status.csv`、`<反应>_missing.txt`）。只下某一个反应：

```powershell
& "D:\论文-AI4S\wt-newrxn\agent\new_reactions\downloads\run_downloads.ps1" -Reactions rwgs
```

PDF 存到 `D:\论文-AI4S\wt-newrxn\agent\new_reactions\pdf\<反应>\`（不进 git）。下完之后告诉我，后面的 OCR、抽取、建模都由脚本和 agent 接着做。

PDH 和 CO₂ 甲烷化已经分别有 50 篇和 37 篇 PDF，这次不用再下；规模化实验要做到 100 篇时，再单独给你 Elsevier 的清单。
