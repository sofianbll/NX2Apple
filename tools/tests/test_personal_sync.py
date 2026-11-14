"""The personal upstream sync stays review-only and follows official NX2Apple."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / '.github/workflows/sync-upstream.yml').read_text(encoding='utf-8')


class PersonalSyncWorkflow(unittest.TestCase):
    def test_merges_official_nx2apple_into_the_personal_branch(self):
        self.assertIn('https://github.com/LNPANDY/NX2Apple.git refs/heads/main', WORKFLOW)
        self.assertIn('ref: local/powera', WORKFLOW)
        self.assertIn('git merge-base --is-ancestor "$UPSTREAM" "$PERSONAL"', WORKFLOW)
        self.assertIn('git merge --no-ff --no-edit "$UPSTREAM"', WORKFLOW)
        self.assertIn('sync/nx2apple-${UPSTREAM:0:7}', WORKFLOW)
        self.assertIn('--base local/powera', WORKFLOW)
        self.assertIn('python3 tools/engine.py check', WORKFLOW)
        self.assertIn('python3 tools/engine.py sync', WORKFLOW)

    def test_has_no_independent_engine_bump_or_publication(self):
        for forbidden in (
            'seedds/nxnative.git refs/heads/main',
            'tools/engine.py bump',
            'publish-experimental',
            'engine-experimental',
            'release_manifest.py publish',
            'gh release',
            'gh pr merge',
            '--auto',
            '--force',
            'git push -f',
            '--no-verify',
            'gh pr reopen',
            'secrets.ENGINE_SIGNING_KEY',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, WORKFLOW)

    def test_recovers_only_the_expected_merge_and_requires_the_ci_token(self):
        self.assertIn('git rev-list --parents -n 1 "$REMOTE"', WORKFLOW)
        self.assertIn('EXPECTED="$REMOTE $PERSONAL $UPSTREAM"', WORKFLOW)
        self.assertIn('git merge-base --is-ancestor "$FIRST" "$PERSONAL"', WORKFLOW)
        self.assertIn('SYNC_TOKEN is required', WORKFLOW)
        self.assertIn('secrets.SYNC_TOKEN', WORKFLOW)
        self.assertNotIn('secrets.SYNC_TOKEN || secrets.GITHUB_TOKEN', WORKFLOW)
        self.assertNotIn('PR creation failed', WORKFLOW)

    def test_macos_credentials_and_exact_pin(self):
        self.assertIn('runs-on: xcode-27', WORKFLOW)
        self.assertIn('DEVELOPER_DIR: /Applications/Xcode_27.2.app/Contents/Developer', WORKFLOW)
        self.assertIn('persist-credentials: false', WORKFLOW)
        job_header = WORKFLOW.split('jobs:', 1)[1].split('steps:', 1)[0]
        self.assertNotIn('GH_TOKEN', job_header)
        self.assertIn('unset SYNC_TOKEN AUTH', WORKFLOW)
        self.assertIn('trap cleanup EXIT', WORKFLOW)
        self.assertIn('if [ "$ACTUAL_PIN" != "$NEW_PIN" ]', WORKFLOW)

    def test_closed_pull_request_is_a_noop(self):
        self.assertIn('--state all', WORKFLOW)
        self.assertIn('Not reopening it or creating another', WORKFLOW)
        self.assertIn('echo "pr_url=$PR_URL" >> "$GITHUB_OUTPUT"', WORKFLOW)

    def test_pre_push_hooks_have_the_existing_ci_python_dependencies(self):
        self.assertIn('uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0', WORKFLOW)
        self.assertIn("python-version: '3.14'", WORKFLOW)
        tests = (ROOT / '.github/workflows/tests.yml').read_text(encoding='utf-8')
        qt = tests.split('  launcher-qt:', 1)[1].split('  triage-scripts:', 1)[0]
        packages = next(line.split('--only-binary=:all: ', 1)[1].rstrip('"')
                        for line in qt.splitlines() if '--only-binary=:all:' in line)
        self.assertIn('python3 -m pip install --only-binary=:all: ' + packages + ' fonttools', WORKFLOW)

    def test_personal_push_triggers_the_existing_ci_workflows(self):
        for name in ('tests.yml', 'build-mac-app.yml'):
            with self.subTest(workflow=name):
                text = (ROOT / '.github/workflows' / name).read_text(encoding='utf-8')
                self.assertIn('branches: [main, local/powera]', text)


if __name__ == '__main__':
    unittest.main()
