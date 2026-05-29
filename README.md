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
ggpsi1psi1g_gpt0p8
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

## part_run 分支：按 set 推进的 DAGMan 工作流

`part_run` 分支新增一套实验性 DAGMan 提交流程。它不改变当前稳定主线，而是新增 per-set DAG：每个 `setN` 自己按顺序执行完整链路。

旧主线的依赖粒度是 stage/job：

```text
job 内所有 set 完成 GEN -> 整个 job 进入 SIM -> 整个 job 进入 DIGI -> ...
```

`part_run` 的依赖粒度是 set：

```text
set1: GEN -> SIM -> DIGI -> HLT -> RECO -> MINIAOD -> NTUPLE
set2: GEN -> SIM -> DIGI -> HLT -> RECO -> MINIAOD -> NTUPLE
...
```

因此某个 `setN` 完成 GEN 后即可进入 SIM，不需要等待同一个 `job_{ProcID}` 的其它 set 完成 GEN。不同 set 之间互不依赖；若某个 set 失败，只会阻断该 set 的后续节点，其它 set 可继续推进。

新增入口脚本：

```text
htcondor/2016HelacOnia/DAG/build_part_run_dag.py
htcondor/2016HelacOnia/DAG/submit_part_run_dag.sh
htcondor/2016HelacOnia/DAG/submit_part_run_dag_range.sh
```

### part_run 提交流程

`part_run` 仍然从已有大 LHE 开始。第一步和主线相同，先切 LHE：

```bash
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/LHE_SPLIT
bash submit_lhe_split_range.sh <process> <job_start> <job_end> [skip_list]
```

这一步完成后应生成：

```text
LHE/{process}/job_{ProcID}/setN.lhe
LHE/{process}/job_{ProcID}/set_list.txt
```

等 LHE split 的 Condor job 全部完成后，进入 `DAG` 目录。`part_run` 不使用旧主线的 `build_stage_subs_range.sh`，而是由 `build_part_run_dag.py` 直接为每个 `setN` 生成 per-set DAG 和对应 `.sub`。

单个 job 只 build，不提交：

```bash
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG
python3 build_part_run_dag.py <process> <ProcID>
```

这会生成：

```text
DAG/part_runs/{process}_job_{ProcID}/part_run_{process}_job_{ProcID}.dag
DAG/part_runs/{process}_job_{ProcID}/submit/{STEP}_setN.sub
DAG/part_logs/{process}_job_{ProcID}/
```

单个 job build 并提交 DAGMan：

```bash
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG
bash submit_part_run_dag.sh <process> <ProcID>
```

批量 build 并提交 DAGMan：

```bash
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG
bash submit_part_run_dag_range.sh <process> <start> <end> [skip_list]
```

因此 `part_run` 的完整批量命令是：

```bash
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/LHE_SPLIT
bash submit_lhe_split_range.sh <process> <start> <end> [skip_list]

# 等 LHE split 全部完成后：
cd /afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia/DAG
bash submit_part_run_dag_range.sh <process> <start> <end> [skip_list]
```

注意：`submit_part_run_dag.sh` 和 `submit_part_run_dag_range.sh` 内部会先调用 `build_part_run_dag.py` 生成 DAG/.sub，然后再 `condor_submit_dag`，所以通常不需要手动单独运行 build。

`part_run` 生成的 DAG 和 `.sub` 存放在：

```text
DAG/part_runs/{process}_job_{ProcID}/
```

对应日志存放在：

```text
DAG/part_logs/{process}_job_{ProcID}/
```

该流程复用现有 worker：

```text
bin/run_gen_condor.sh
bin/run_sim_input_condor.sh
bin/run_digi_input_condor.sh
bin/run_hlt_input_condor.sh
bin/run_reco_input_condor.sh
bin/run_miniaod_input_condor.sh
bin/run_ntuple_input_condor.sh
```

注意：真实 Condor 运行仍应在 AFS 提交区执行。若在本项目中修改 `part_run` 脚本，需要同步回：

```text
/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia
```

### part_run 输出检查与残余清理

`part_run` 的检查单位是 `process + job_{ProcID} + setN`。成功判据只看最终文件是否存在：

```text
NTUPLE/{process}/job_{ProcID}/setN.root
```

若该 NTUPLE ROOT 不存在，检查脚本会从 `GEN -> ... -> NTUPLE` 查找最后一个仍存在的 step，并把下一步标记为失败步骤。例如最后存在 `SIM/setN.root`，则失败步骤为 `DIGI`。

检查命令：

```bash
python3 output_check/part_run/check_part_run_outputs.py \
  --process <process> \
  --start <job_start> \
  --end <job_end> \
  [--skip <skip_list>]
```

报告输出：

```text
output_check/part_run/{process}/job{start}_{end}.md
```

残余清理脚本根据检查报告中的 `failed_step` 清理该 set 在失败步骤之前两步内的 ROOT：

```text
GEN 失败：不删除
SIM 失败：只删除 GEN/setN.root
DIGI 失败：删除 GEN/setN.root 和 SIM/setN.root
HLT 失败：删除 SIM/setN.root 和 DIGI/setN.root
...
```

默认 dry-run：

```bash
python3 output_check/part_run/cleanup_part_run_residuals.py \
  --process <process> \
  --report output_check/part_run/<process>/job<start>_<end>.md
```

确认后真实删除：

```bash
python3 output_check/part_run/cleanup_part_run_residuals.py \
  --process <process> \
  --report output_check/part_run/<process>/job<start>_<end>.md \
  --apply
```
