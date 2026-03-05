from src.commands import repl_args


def test_build_cli_args_uses_spec_positional_defaults():
    args = repl_args.build_cli_args(
        "addon-deps",
        [":addon", "sample_addon"],
        value_parser=lambda value: value,
    )

    assert args == ["list", "sample_addon"]


def test_apply_positional_defaults_is_generic_for_specs_without_defaults():
    args = repl_args.build_cli_args(
        "test",
        [":addon", "sample_addon"],
        value_parser=lambda value: value,
    )

    assert args == ["sample_addon"]
