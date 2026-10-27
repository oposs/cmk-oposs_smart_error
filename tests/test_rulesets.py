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
