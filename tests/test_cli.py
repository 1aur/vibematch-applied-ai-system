from src.main import main


def test_cli_returns_safe_error_for_invalid_energy(capsys):
    exit_code = main(
        [
            "--genre",
            "pop",
            "--mood",
            "happy",
            "--energy",
            "1.2",
            "--non-acoustic",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "could not complete the request" in captured.err
    assert "between 0.0 and 1.0" in captured.err
    assert "Traceback" not in captured.err
