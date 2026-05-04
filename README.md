# MC_Maker

本仓库保存 2016 SPS MC 生产中从 HELAC-Onia LHE 到 NTUPLE 的轻量级工作流代码。主流程是：

```text
大 LHE -> LHE 切分 -> GEN -> SIM -> DIGI -> HLT -> RECO -> MINIAOD -> NTUPLE
```

仓库只应保存可复用的脚本和 CMSSW 配置片段。大体积 LHE/ROOT 输出、Condor 日志、自动生成的 `.sub`、DAG rescue 文件、完整 CMSSW release、交接文档和 Codex 相关文件都不上传。

## 支持的过程

当前流程使用的过程名：

```text
ggpsi1psi1
ggpsi1psi1g
```

每个 `process + ProcID` 对应的大 LHE 默认路径为：

```text
/afs/cern.ch/user/l/leyao/work/26JJ/HelacOnia/packaged_runs_test/{process}/job_{ProcID}/PROC_HO_0/P0_calc_0/output/sample{process}.lhe
```

## 主工作流

以下命令需要在 CERN 环境中运行，并要求 AFS/EOS、CMSSW、`cmssw-el7` 和 HTCondor 可用。

1. 把大 LHE 切成 250 events 一个的小 LHE：

```bash
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/LHE_SPLIT
bash submit_lhe_split_range.sh <process> <job_start> <job_end> [skip_list]
```

2. 等 LHE split 的 Condor job 全部完成后，生成每一步的 `.sub`：

```bash
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG
bash build_stage_subs_range.sh <process> <job_start> <job_end> [skip_list]
```

3. 提交 DAGMan，运行 `GEN -> SIM -> DIGI -> HLT -> RECO -> MINIAOD -> NTUPLE`：

```bash
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG
bash submit_workflow_dag_range.sh <process> <job_start> <job_end> [skip_list]
```

`skip_list` 可选，格式例如：

```text
3,7,job_12
```

单个 job 可直接提交：

```bash
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG
bash submit_workflow_dag.sh <process> <ProcID>
```

## 存储规则

整个流程统一使用 `process/job_{ProcID}/setN` 命名：

```text
LHE/{process}/job_{ProcID}/setN.lhe
GEN/{process}/job_{ProcID}/setN.root
SIM/{process}/job_{ProcID}/setN.root
DIGI/{process}/job_{ProcID}/setN.root
HLT/{process}/job_{ProcID}/setN.root
RECO/{process}/job_{ProcID}/setN.root
MINIAOD/{process}/job_{ProcID}/setN.root
NTUPLE/{process}/job_{ProcID}/setN.root
```

各步骤所在 CMSSW 目录：

```text
LHE, GEN:                  HelacOnia2016/CMSSW_10_6_20_patch1/src
SIM, DIGI, RECO, MINIAOD:  HelacOnia2016/CMSSW_10_6_17_patch1/src
HLT:                       HelacOnia2016/CMSSW_8_0_33_UL/src
NTUPLE:                    HelacOnia2016/CMSSW_10_6_20/src
```

## 输出检查脚本

检查每个 job 首次失败在哪一步：

```bash
python3 output_check/check_pipeline_outputs.py --process <process> --start <job_start> --end <job_end> [--skip <skip_list>]
```

检查失败原因摘要：

```bash
python3 output_check/check_failure_reasons.py --process <process> --start <job_start> --end <job_end> [--skip <skip_list>]
```

根据检查报告清理失败 job 的前两步 ROOT：

```bash
python3 output_check/cleanup_prev_steps_roots.py --process <process> --report output_check/<process>/job<start>_<end>.md
```

合并 NTUPLE 输出：

```bash
python3 output_check/merge_ntuple_jobs.py --process <process> --begin <job_start> --end <job_end>
```

## 仍在 AFS 提交区的关键脚本

当前主 DAGMan 提交流程的很多脚本仍在 AFS，而不是本 EOS 项目目录。若要让 GitHub 仓库完整复现流程，应把这些文件复制到仓库内，例如 `htcondor/2016HelacOnia/` 后再提交。

```text
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/config/paths.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/dag_stage_driver.py
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/build_max10_test_subs.py
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/prepare_lhe_inputs.py
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/run_lhe_split_condor.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/run_gen_condor.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/run_sim_condor.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/run_digi_condor.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/run_hlt_condor.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/run_reco_condor.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/run_miniaod_condor.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/bin/run_ntuple_condor.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/LHE_SPLIT/make_lhe_split_submit.py
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/LHE_SPLIT/submit_lhe_split_range.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG/workflow.dag
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG/workflow_max10_test.dag
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG/build_stage_subs_range.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG/submit_workflow_dag.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG/submit_workflow_dag_range.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG/submit_max10_test_dag.sh
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/GEN/make_gen_submit.py
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/SIM/make_sim_submit.py
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DIGI/make_digi_submit.py
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/HLT/make_hlt_submit.py
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/RECO/make_reco_submit.py
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/MINIAOD/make_miniaod_submit.py
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/NTUPLE/make_ntuple_submit.py
```

旧的 mixed/retry 脚本可以保留用于追溯，但当前主线是这里描述的 DAGMan 链路。

## GitHub 同步建议

第一次同步到 GitHub：

```bash
cd /eos/home-l/leyao/26JJ/MC_Maker
git init
git add .gitignore README.md output_check/*.py \
  HelacOnia2016/CMSSW_10_6_20_patch1/src/GEN.py \
  HelacOnia2016/CMSSW_10_6_20_patch1/src/split_lhe.py \
  HelacOnia2016/CMSSW_10_6_17_patch1/src/SIM.py \
  HelacOnia2016/CMSSW_10_6_17_patch1/src/DIGI.py \
  HelacOnia2016/CMSSW_8_0_33_UL/src/HLT.py \
  HelacOnia2016/CMSSW_10_6_17_patch1/src/RECO.py \
  HelacOnia2016/CMSSW_10_6_17_patch1/src/MINIAOD.py
git commit -m "Add lightweight MC DAGMan workflow"
git branch -M main
git remote add origin git@github.com:LekaiYao/MC_Maker.git
git push -u origin main
```

正式推送前，建议先把 AFS 关键脚本复制进仓库中的固定目录并一起提交。

## 提交区脚本同步规则

`htcondor/2016HelacOnia/` 是 AFS 提交区主工作流脚本的 GitHub 镜像。真实 Condor 生产仍在 AFS 提交区运行：

```text
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia
```

同步原则：

```text
AFS 提交区 -> 本项目 htcondor/2016HelacOnia/ -> GitHub
GitHub/本项目修改 -> AFS 提交区 -> 真实 Condor 运行
```

也就是说：

1. 如果在 AFS 提交区修改了 DAGMan、submit 生成器或 worker 脚本，需要先把关键脚本拷贝回本项目的 `htcondor/2016HelacOnia/`，再提交到 GitHub。
2. 如果在本项目/GitHub 中修改了提交区逻辑，需要把对应文件同步回 AFS 提交区后，才能用于真实生产提交。
3. 不要把 `logs/`、`submit/`、`runs/`、`.sub`、`.log`、`.out`、`.err`、rescue 文件或 ROOT/LHE 数据产物纳入 GitHub。

当前主线入口脚本：

```text
htcondor/2016HelacOnia/LHE_SPLIT/submit_lhe_split_range.sh
htcondor/2016HelacOnia/DAG/build_stage_subs_range.sh
htcondor/2016HelacOnia/DAG/submit_workflow_dag_range.sh
```

当前主线 DAG 和 stage driver：

```text
htcondor/2016HelacOnia/DAG/workflow.dag
htcondor/2016HelacOnia/bin/dag_stage_driver.py
```
