# AGENTS.md

本仓库是一个用 Python + XeLaTeX 开发的打印手账/书籍生成器（`techo`）。本文档规定**全部 GitHub 提交流程**：账号分工、issue、PR、review 与合并，一律通过 GitHub CLI（`gh`）完成。

## 开发阶段

项目当前处于**开发阶段**（未发布、无外部用户）。因此：

- **允许破坏性重构**：可以自由调整架构、模块划分、数据结构与命名，不必为旧代码维持兼容。
- **不做生成物/接口向后兼容**：`outputs/` 下的成品、CLI 参数与 LaTeX 模板约定均可随意变更或作废——一切皆可由源码重新生成。

## 账号分工

仓库协作使用两个 GitHub 账号，职责严格分离：

| 账号 | 角色 | 职责 |
| --- | --- | --- |
| `asinkLuno` | 开发者 | **只交代码**：开发、commit、push、创建 PR、处理 review 意见 |
| `starmountain1997` | 仓库管理者 / 规划者 | **提 issue**（规划需求）、**review 代码**（approve / request changes）、**合并 PR** |

> 一句话：`asinkLuno` 出活，`starmountain1997` 把关。代码永远由 `asinkLuno` 提交；issue、评审、合并永远由 `starmountain1997` 执行。

## 账号切换（gh auth switch）

两个账号都已通过 `gh` 认证，用 `gh auth switch` 切换活跃账号：

```bash
gh auth switch --user asinkLuno          # 切到开发者账号（交代码）
gh auth switch --user starmountain1997   # 切到管理者账号（提 issue / review / 合并）
gh auth status                           # 查看当前活跃账号与 token 权限
gh api user --jq .login                  # 快速确认当前是谁
```

> git 的 push 凭证跟随 `gh` 活跃账号（credential helper 指向 `gh auth git-credential`），
> 所以**切完账号再 push，提交/推送方就是该账号**。执行任何 GitHub 操作前，先确认当前账号正确。

## 铁律

- 永远用 `asinkLuno` 提交代码：commit、push、`gh pr create`。
- 永远用 `starmountain1997` 提交 issue、review 代码、合并 PR。
- `asinkLuno` 不合并 PR、不 approve 自己的 PR；`starmountain1997` 不直接写代码、不 push 功能分支。
- 仓库级 git 身份固定为 `asinkLuno <202598718+asinkLuno@users.noreply.github.com>`，不要修改。
- PR 一律从功能分支发往 `main`，不在 `main` 上直接提交；合并用 squash。

## 提代码流程（asinkLuno）

```bash
# 0. 确认是开发者账号
gh auth switch --user asinkLuno
gh api user --jq .login                    # => asinkLuno

# 1. 从最新的 main 拉功能分支
git checkout main && git pull
git checkout -b feat/xxx

# 2. 开发、提交（提交身份自动是 asinkLuno）
git add -A && git commit -m "feat(xxx): 功能描述"

# 3. 推送分支并创建 PR，请求 starmountain1997 review
git push -u origin feat/xxx
gh pr create --repo asinkLuno/techo --base main --head feat/xxx \
  --title "feat(xxx): 功能描述" --body "见 issue #N" --reviewer starmountain1997
```

## 提 issue 流程（starmountain1997 —— 规划者）

规划、记录需求、抛讨论，用管理者账号：

```bash
gh auth switch --user starmountain1997

# 创建 issue（带标签、指派给 asinkLuno 开发）
gh issue create --repo asinkLuno/techo \
  --title "讨论：月球手账的时间体系如何分层" \
  --body "背景 / 目标 / 验收标准" \
  --label "enhancement" --assignee asinkLuno

# 列出 / 查看 issue
gh issue list --repo asinkLuno/techo --state open
gh issue view 10 --repo asinkLuno/techo
```

开发时在 commit 与 PR 正文里引用 issue 编号（如 `issue #10`），形成「issue 规划 → PR 实现 → review 关闭」的闭环。

## Review 代码流程（starmountain1997 —— 管理者）

```bash
gh auth switch --user starmountain1997

gh pr list --repo asinkLuno/techo                    # 列出待 review 的 PR
gh pr view 12 --repo asinkLuno/techo                 # 看详情（状态、review 意见）
gh pr diff 12 --repo asinkLuno/techo                 # 看代码 diff

gh pr review 12 --repo asinkLuno/techo --comment --body "具体评论"          # 评论
gh pr review 12 --repo asinkLuno/techo --request-changes --body "修改意见"  # 打回
gh pr review 12 --repo asinkLuno/techo --approve                             # 通过
```

## 处理 review 意见（asinkLuno）

```bash
gh auth switch --user asinkLuno
# 在同一个功能分支上改
git commit -am "fix(xxx): 处理 review #12 意见"
git push                            # 同一分支 push，PR 自动更新
# 改完后可让管理者重新 review：
gh pr edit 12 --repo asinkLuno/techo --body "已按 review 意见修改，请复审"
```

## 合并 PR 流程（starmountain1997）

```bash
gh auth switch --user starmountain1997

# 确认已 approve 后再合并（squash + 删分支）
gh pr view 12 --repo asinkLuno/techo --json reviewDecision --jq .reviewDecision   # => APPROVED
gh pr merge 12 --repo asinkLuno/techo --squash --delete-branch
```

合并后如该 PR 关联了 issue，用管理者账号关闭：

```bash
gh issue close 10 --repo asinkLuno/techo --comment "已通过 PR #12 完成"
```

## 命令速查

```
gh auth switch --user asinkLuno          开发者账号（交代码）
gh auth switch --user starmountain1997   管理者账号（issue / review / 合并）
gh pr create --reviewer starmountain1997 asinkLuno 建 PR 并请求 review
gh issue create --assignee asinkLuno     starmountain1997 提 issue 交给开发
gh pr review <pr> --approve              starmountain1997 通过
gh pr review <pr> --request-changes      starmountain1997 打回
gh pr merge <pr> --squash --delete-branch starmountain1997 合并
```

## 完整迭代示例

1. **规划（starmountain1997）**：`gh issue create` 提出需求，指派 `asinkLuno`。
2. **开发（asinkLuno）**：切账号 → 拉分支 → 实现 → commit → `gh pr create --reviewer starmountain1997`。
3. **评审（starmountain1997）**：`gh pr view/diff` 审查 → approve 或 request changes。
4. **返工（asinkLuno）**：按意见改，push 同一分支；满意后管理者 approve。
5. **合并（starmountain1997）**：`gh pr merge --squash --delete-branch` → 关闭关联 issue。
