from pathlib import Path


def test_fresh_host_rehearsal_is_single_documented_path() -> None:
    script = Path("infra/scripts/rehearsal-host-restore.sh").read_text()
    playbook = Path("infra/ansible/site.yml").read_text()

    assert "ansible-playbook" in script
    assert "infra/ansible/site.yml" in script
    assert "REHEARSAL_INVENTORY" in script
    assert "REHEARSAL_LIMIT" in script
    assert "REHEARSAL_SSH_TARGET" in script
    assert "/etc/palvelut/backup.env" in script
    assert "infra/scripts/restore-drill.sh" in script
    assert "source /etc/palvelut/backup.env" in script
    assert "palvelut_backup_environment_file is defined" in playbook
    assert 'dest: "{{ palvelut_secret_dir }}/backup.env"' in playbook
    assert 'mode: "0600"' in playbook
    assert "no_log: true" in playbook
