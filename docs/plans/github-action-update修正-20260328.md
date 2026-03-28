.github/workflows/update.yml
の実行で、以下のエラー

Run git config user.name "github-actions[bot]"
[main 3f2be51] Update: 2026-03-28 23:00
 17 files changed, 3104 insertions(+), 784 deletions(-)
 delete mode 100644 docs/archive/2026-03-28.html
 create mode 100644 docs/archive/2026-03-28_23.html
 create mode 100644 docs/data/2026-03-28_23.json
 delete mode 100644 docs/pagefind/fragment/ja_3a13534.pf_fragment
 create mode 100644 docs/pagefind/fragment/ja_fa95654.pf_fragment
 create mode 100644 docs/pagefind/index/ja_2ebf1f6.pf_index
 delete mode 100644 docs/pagefind/index/ja_9ea27f7.pf_index
 create mode 100644 docs/pagefind/pagefind.ja_758b94b0be.pf_meta
 delete mode 100644 docs/pagefind/pagefind.ja_9b6c106d53.pf_meta
Push attempt 1/3
From https://github.com/aa-0921/hn-matome
 * branch            main       -> FETCH_HEAD
   79ed96a..900c90c  main       -> origin/main
Auto-merging docs/about.html
CONFLICT (modify/delete): docs/archive/2026-03-28.html deleted in 3f2be51 (Update: 2026-03-28 23:00) and modified in HEAD.  Version HEAD of docs/archive/2026-03-28.html left in tree.
Auto-merging docs/index.html
Auto-merging docs/privacy.html
Rebasing (1/1)
error: could not apply 3f2be51... Update: 2026-03-28 23:00
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: run "git rebase --skip".
hint: To abort and get back to the state before "git rebase", run "git rebase --abort".
hint: Disable this message with "git config set advice.mergeConflict false"
Could not apply 3f2be51... # Update: 2026-03-28 23:00
Push attempt 2/3
From https://github.com/aa-0921/hn-matome
 * branch            main       -> FETCH_HEAD
Auto-merging docs/about.html
CONFLICT (modify/delete): docs/archive/2026-03-28.html deleted in 3f2be51 (Update: 2026-03-28 23:00) and modified in HEAD.  Version HEAD of docs/archive/2026-03-28.html left in tree.
Auto-merging docs/index.html
Auto-merging docs/privacy.html
Rebasing (1/1)
error: could not apply 3f2be51... Update: 2026-03-28 23:00
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: run "git rebase --skip".
hint: To abort and get back to the state before "git rebase", run "git rebase --abort".
hint: Disable this message with "git config set advice.mergeConflict false"
Could not apply 3f2be51... # Update: 2026-03-28 23:00
Push attempt 3/3
From https://github.com/aa-0921/hn-matome
 * branch            main       -> FETCH_HEAD
Auto-merging docs/about.html
CONFLICT (modify/delete): docs/archive/2026-03-28.html deleted in 3f2be51 (Update: 2026-03-28 23:00) and modified in HEAD.  Version HEAD of docs/archive/2026-03-28.html left in tree.
Auto-merging docs/index.html
Auto-merging docs/privacy.html
Rebasing (1/1)
error: could not apply 3f2be51... Update: 2026-03-28 23:00
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: run "git rebase --skip".
hint: To abort and get back to the state before "git rebase", run "git rebase --abort".
hint: Disable this message with "git config set advice.mergeConflict false"
Could not apply 3f2be51... # Update: 2026-03-28 23:00
Push failed after 3 attempts
Error: Process completed with exit code 1.


