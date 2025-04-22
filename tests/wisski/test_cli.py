from wisskas.cli.main import main


input_args = ["tests/data/releven_assertions_20240821.xml"]


def run_cli(*args):
    main([*input_args, *args])


def test_cli_endpoints():
    """crash tests"""
    run_cli("endpoints", "--endpoint-exclude-fields", "external_authority")
    run_cli(
        "endpoints", "--endpoint-exclude-fields", "external_authority", "--git-endpoint"
    )


def test_cli_paths():
    """crash tests"""
    run_cli("paths", "--flat")
    run_cli("paths", "--flat", "--all")
    run_cli("paths", "--nested")
    run_cli("paths", "--nested", "--all")
