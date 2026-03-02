def test_operator_idname_format():
    addon_name = "{{addon_name}}"
    operator_idname = f"{addon_name}.basic_operator"
    assert operator_idname.endswith(".basic_operator")
