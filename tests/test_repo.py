# -*- coding: utf-8 -*-
"""Test ghim bản code (src/repo.py).

Điều quan trọng nhất được khoá ở đây: **không bao giờ chạy trên bản code không rõ là bản nào**.
Thư mục không đúng commit đã ghim thì phải dừng, chứ không im lặng chạy tiếp; commit không nằm
trên nhánh cho phép thì phải cảnh báo (hoặc là lỗi, khi preflight yêu cầu).

Các ca ở đây chạy OFFLINE: chúng dùng chính repo đang mở và một repo tạm, không gọi GitHub (phần
kéo code từ mạng được kiểm ở P5 DoD bằng một lượt chạy thật trên Colab).

Chạy: python -m unittest discover -s tests
"""

import tempfile
import unittest
from pathlib import Path

from src import paths, repo


class TestGitHelpers(unittest.TestCase):
    def test_current_sha_matches_git(self):
        sha = repo.current_sha()
        self.assertRegex(sha, r"^[0-9a-f]{40}$")
        code, output = repo.run_git(["rev-parse", "HEAD"], cwd=paths.root())
        self.assertEqual(code, 0)
        self.assertEqual(sha, output.strip())

    def test_is_repo_true_for_project_and_false_for_temp(self):
        self.assertTrue(repo.is_repo())
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(repo.is_repo(folder))

    def test_current_sha_of_non_repo_is_empty(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(repo.current_sha(folder), "")

    def test_is_ancestor_of_itself(self):
        sha = repo.current_sha()
        self.assertTrue(repo.is_ancestor(sha, "HEAD"))
        self.assertFalse(repo.is_ancestor("0" * 40, "HEAD"))
        self.assertFalse(repo.is_ancestor("", "HEAD"))

    def test_ref_exists(self):
        self.assertTrue(repo.ref_exists("HEAD"))
        self.assertFalse(repo.ref_exists("khong-co-nhanh-nay"))
        self.assertFalse(repo.ref_exists(""))

    def test_plans_are_ordered_from_cheap_to_expensive(self):
        plans = repo.plans("https://example.invalid/repo.git", "a" * 40)
        self.assertEqual([name for name, _steps in plans],
                         ["fetch theo sha", "clone rút gọn rồi checkout"])
        for _name, steps in plans:
            for args, required in steps:
                self.assertIsInstance(args, list)
                self.assertIsInstance(required, bool)


class TestPrepare(unittest.TestCase):
    def test_missing_url_or_sha_is_an_error(self):
        for url, sha in (("", "a" * 40), ("https://example.invalid/r.git", "")):
            with self.assertRaises(repo.RepoError):
                repo.prepare(url, sha)

    def test_uses_the_checkout_that_is_already_correct(self):
        """Máy cá nhân thường ở đây: đúng commit rồi thì không cần mạng."""
        info = repo.prepare("https://example.invalid/repo.git", repo.current_sha(),
                            branch="experiment")
        self.assertEqual(info["action"], "dùng bản code đang có")
        self.assertEqual(info["dir"], str(paths.root()))

    def test_warns_when_the_allowed_branch_is_unknown_here(self):
        """Thiếu thông tin về nhánh thì cảnh báo, không báo lỗi: máy cá nhân hay ở trường hợp này."""
        info = repo.prepare("https://example.invalid/repo.git", repo.current_sha(),
                            branch="nhanh-khong-ton-tai")
        self.assertIn("không kiểm được", " ".join(info["warnings"]))

    def test_unknown_branch_is_never_a_hard_error(self):
        info = repo.prepare("https://example.invalid/repo.git", repo.current_sha(),
                            branch="nhanh-khong-ton-tai", require_branch=True)
        self.assertEqual(info["action"], "dùng bản code đang có")

    def test_unreachable_commit_stops_instead_of_running_anyway(self):
        """Không kéo được đúng commit thì DỪNG, và nói rõ đã thử những cách nào."""
        with tempfile.TemporaryDirectory() as folder:
            origin = Path(folder) / "origin"
            origin.mkdir()
            repo.run_git(["init", "-q"], cwd=origin)
            repo.run_git(["config", "user.email", "test@example.invalid"], cwd=origin)
            repo.run_git(["config", "user.name", "test"], cwd=origin)
            (origin / "file.txt").write_text("x\n", encoding="utf-8")
            repo.run_git(["add", "file.txt"], cwd=origin)
            repo.run_git(["commit", "-q", "-m", "first"], cwd=origin)

            dest = Path(folder) / "checkout"
            with self.assertRaises(repo.RepoError) as caught:
                repo.prepare(str(origin), "f" * 40, dest=dest)
            message = str(caught.exception)
            self.assertIn("Không kéo được commit đã ghim", message)
            self.assertIn("fetch theo sha", message)
            self.assertIn("clone rút gọn rồi checkout", message)


class TestExistingRepo(unittest.TestCase):
    """Máy cá nhân: repo đã có sẵn, đúng remote -> chỉ lấy thêm commit đã ghim.

    Hai lỗi bị khoá ở đây, cả hai đều đã xảy ra thật (25/09/2026):
      - `git remote remove origin` + `remote add` xoá hết ref `origin/*`, nên lần kiểm "commit đã
        ghim có nằm trên nhánh không" không còn gì để kiểm (chỉ in cảnh báo);
      - `git fetch --depth 1` biến repo đầy đủ thành repo NÔNG: `git rev-list --count HEAD` của
        repo cá nhân tụt từ 124 commit xuống 3.
    """

    def make_pair(self, folder):
        """Một kho `origin` hai commit, và một bản clone của nó (giống repo máy cá nhân)."""
        origin = Path(folder) / "origin"
        origin.mkdir()
        repo.run_git(["init", "-q"], cwd=origin)
        repo.run_git(["config", "user.email", "test@example.invalid"], cwd=origin)
        repo.run_git(["config", "user.name", "test"], cwd=origin)
        (origin / "file.txt").write_text("mot\n", encoding="utf-8")
        repo.run_git(["add", "file.txt"], cwd=origin)
        repo.run_git(["commit", "-q", "-m", "first"], cwd=origin)
        first = repo.run_git(["rev-parse", "HEAD"], cwd=origin)[1].strip()
        (origin / "file.txt").write_text("hai\n", encoding="utf-8")
        repo.run_git(["commit", "-q", "-am", "second"], cwd=origin)
        clone = Path(folder) / "clone"
        repo.run_git(["clone", "-q", str(origin), str(clone)])
        return origin, clone, first

    def test_plans_offer_the_existing_repo_first(self):
        with tempfile.TemporaryDirectory() as folder:
            origin, clone, _first = self.make_pair(folder)
            names = [name for name, _steps in repo.plans(str(origin), "a" * 40, clone)]
            self.assertEqual(names[0], "dùng repo đang có")
            self.assertNotIn("remote", " ".join(str(args) for args in
                                                 repo.plans(str(origin), "a" * 40, clone)[0][1]))

    def test_plans_do_not_offer_it_when_origin_is_somewhere_else(self):
        with tempfile.TemporaryDirectory() as folder:
            _origin, clone, _first = self.make_pair(folder)
            names = [name for name, _steps in repo.plans("https://example.invalid/r.git", "a" * 40,
                                                         clone)]
            self.assertEqual(names, ["fetch theo sha", "clone rút gọn rồi checkout"])

    def test_fetching_an_older_commit_keeps_remotes_and_full_history(self):
        with tempfile.TemporaryDirectory() as folder:
            origin, clone, first = self.make_pair(folder)
            before = repo.run_git(["branch", "-r"], cwd=clone)[1].split()
            self.assertTrue(before, "bản clone phải có ref origin/*")

            info = repo.prepare(str(origin), first, dest=clone)
            self.assertEqual(info["action"], "dùng repo đang có")
            self.assertEqual(repo.current_sha(clone), first)
            self.assertEqual(repo.run_git(["branch", "-r"], cwd=clone)[1].split(), before)
            self.assertFalse((clone / ".git" / "shallow").exists(),
                             "không được biến repo đầy đủ thành repo nông")

    def test_a_commit_that_is_not_on_the_remote_stops_without_touching_the_repo(self):
        with tempfile.TemporaryDirectory() as folder:
            origin, clone, _first = self.make_pair(folder)
            before = repo.run_git(["branch", "-r"], cwd=clone)[1].split()
            with self.assertRaises(repo.RepoError) as caught:
                repo.prepare(str(origin), "f" * 40, dest=clone)
            self.assertIn("Không lấy được commit đã ghim", str(caught.exception))
            self.assertEqual(repo.run_git(["branch", "-r"], cwd=clone)[1].split(), before)


if __name__ == "__main__":
    unittest.main()
