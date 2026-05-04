# AGENTS.md

## 项目功能

本项目用于管理 2016 SPS MC 生产中从 HELAC-Onia 大 LHE 文件到 NTUPLE 的轻量级代码与 Condor/DAGMan 工作流。

主流程：

```text
大 LHE -> LHE 切分 -> GEN -> SIM -> DIGI -> HLT -> RECO -> MINIAOD -> NTUPLE
```

项目本体只保存脚本和 CMSSW 配置片段，不保存大体积数据产物。

## 关键目录

- GitHub 工作区：`/eos/home-l/leyao/26JJ/MC_Maker`
- AFS 提交区：`/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia`
- 提交区镜像：`htcondor/2016HelacOnia/`
- 交接文档：`docs/handoff.md`，仅作为本地上下文，不上传 GitHub

## 当前主线工作流

真实生产提交仍从 AFS 提交区运行：

```bash
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/LHE_SPLIT
bash submit_lhe_split_range.sh <process> <start> <end> [skip_list]

cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG
bash build_stage_subs_range.sh <process> <start> <end> [skip_list]
bash submit_workflow_dag_range.sh <process> <start> <end> [skip_list]
```

主线依赖：

```text
config/paths.sh
common/submit_utils.py
bin/dag_stage_driver.py
bin/prepare_lhe_inputs.py
bin/run_*_input_condor.sh
LHE_SPLIT/make_lhe_split_submit.py
DAG/workflow.dag
DAG/build_stage_subs_range.sh
DAG/submit_workflow_dag.sh
DAG/submit_workflow_dag_range.sh
*/make_*_submit.py
```

## 同步规则

每次处理提交区代码时必须保持 AFS 和 GitHub 镜像一致。

- 如果在 AFS 提交区修改了主工作流脚本，先复制回本项目 `htcondor/2016HelacOnia/`，再 `git commit` 和 `git push`。
- 如果在本项目或 GitHub 修改了提交区逻辑，必须把对应文件同步回 AFS 提交区后，才能用于真实 Condor 提交。
- 不要把 Condor 运行产物提交到 GitHub，包括 `logs/`、`submit/`、`runs/`、`.sub`、`.log`、`.out`、`.err`、rescue 文件。
- 不要提交 ROOT/LHE 数据文件或完整 CMSSW release 运行产物。
- 旧工作流/遗留脚本目前不清理；但 GitHub 主线镜像只保存当前 DAGMan 主工作流必需脚本。

## 修改原则

- 默认做最小修改，避免改动物理配置。
- CMSSW 配置文件只做接口和路径参数相关改造，不随意改物理设置。
- 提交前检查 `git status --short`，确认没有数据、日志、docs/handoff.md 或临时文件进入索引。
- 真实 batch 问题优先查 `.log/.out/.err`，不要只根据输出文件大小判断。
