"""The rule forms build, and every check default has a matching form field."""

import importlib.util
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "local/lib/python3/cmk_addons/plugins/oposs_smart_error"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def rulesets():
    return _load(PLUGIN / "rulesets/oposs_smart_error.py", "test_oposs_smart_error_rulesets")


@pytest.fixture(scope="module")
def check():
    return _load(PLUGIN / "agent_based/oposs_smart_error.py", "test_oposs_smart_error_check_rs")


def test_bms_defaults_match_form(rulesets, check):
    form = rulesets.rule_spec_oposs_smart_bms.parameter_form()
    assert set(check.BMS_DEFAULT_PARAMETERS) == set(form.elements)
    assert check.check_plugin_oposs_smart_bms.check_ruleset_name == rulesets.rule_spec_oposs_smart_bms.name


def test_bms_form_prefills_match_defaults(rulesets, check):
    form = rulesets.rule_spec_oposs_smart_bms.parameter_form()
    for key, default in check.BMS_DEFAULT_PARAMETERS.items():
        spec = form.elements[key].parameter_form
        prefill = getattr(spec, "prefill_fixed_levels", None) or spec.prefill
        expected = default[1] if isinstance(default, tuple) else default
        assert prefill.value == expected, key


def test_error_form_has_grown_defects(rulesets):
    form = rulesets.rule_spec_oposs_smart_error.parameter_form()
    assert "grown_defects_abs" in form.elements


def test_bakery_timeout_has_a_minimum():
    # A timeout of 0 makes every smartctl call fail at once
    from cmk.rulesets.v1.form_specs import validators
    bakery = _load(PLUGIN / "rulesets/ruleset_oposs_smart_error_bakery.py", "test_oposs_smart_error_bakery_rs")
    timeout = bakery.rule_spec_oposs_smart_error_bakery.parameter_form().elements["timeout"].parameter_form
    ranges = [v.range for v in (timeout.custom_validate or ()) if isinstance(v, validators.NumberInRange)]
    assert ranges and ranges[0][0] >= 1


def test_bakery_form_prefills_match_bakery_defaults():
    import json
    bakery_rs = _load(PLUGIN / "rulesets/ruleset_oposs_smart_error_bakery.py", "test_oposs_smart_error_bakery_rs")
    bakery = _load(ROOT / "local/lib/python3/cmk/base/cee/plugins/bakery/oposs_smart_error.py",
                   "test_oposs_smart_error_bakery")
    form = bakery_rs.rule_spec_oposs_smart_error_bakery.parameter_form()
    files = list(bakery.get_oposs_smart_error_files({}))
    (config,) = [f for f in files if "lines" in f.kwargs]
    (plugin,) = [f for f in files if "lines" not in f.kwargs]
    baked = dict(json.loads("\n".join(config.kwargs["lines"])), interval=plugin.kwargs["interval"])
    assert set(form.elements) == set(baked)
    for key, default in baked.items():
        assert form.elements[key].parameter_form.prefill.value == default, key
