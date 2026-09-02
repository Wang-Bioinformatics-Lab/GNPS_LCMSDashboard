from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_gunicorn_access_log_uses_container_stdout():
    run_server = (REPOSITORY_ROOT / "run_server.sh").read_text()

    assert "--access-logfile -" in run_server
    assert "/app/logs/access.log" not in run_server


def test_docker_stdout_logs_are_rotated():
    compose = (REPOSITORY_ROOT / "docker-compose.yml").read_text()

    assert 'max-size: "10m"' in compose
    assert 'max-file: "3"' in compose
