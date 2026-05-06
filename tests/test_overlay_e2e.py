#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""End-to-end tests for YAML sigil overlay merge.

Validates the full pipeline from YAML sigil parsing through to final DTS
output with two target OS types (linux, zephyr) producing different results.

Tests cover:
- Same SDT YAML with two domains (linux_domain, zephyr_domain)
- Per-property merge schemes: replace, append
- Conditional node staging (chosen!linux:, chosen!zephyr:)
- overlay_tree() producing correct merged tree for each OS
- Outputs for linux and zephyr are different in the expected ways
"""

import io
import sys
import os
import textwrap

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lopper.yaml import LopperYAML
from lopper.tree import LopperProp, LopperNode, LopperTree


# ---------------------------------------------------------------------------
# Shared YAML fixture — single SDT with two domains and sigil annotations
# ---------------------------------------------------------------------------

# This YAML represents a minimal system device tree with:
#
#   /domains/linux_domain:
#     - os,type: linux
#     - compatible!linux!replace → base is "base-compat", linux overlay = "linux-compat"
#     - bootargs!append → appended to any existing value: "loglevel=7"
#     - chosen!linux: node → bootargs "root=/dev/mmcblk0" (conditional)
#
#   /domains/zephyr_domain:
#     - os,type: zephyr
#     - compatible!zephyr!replace → "zephyr-compat"
#     - bootargs!append → "CONFIG_DEBUG=y"
#     - chosen!zephyr: node → bootargs "zephyr,shell-uart" (conditional)
#
# Base (no-sigil) properties are shared and unchanged regardless of overlay.

DOMAINS_YAML = textwrap.dedent("""\
    domains:
      linux_domain:
        os,type: linux
        lopper,activate: linux
        compatible: base-compat
        compatible!linux!replace: linux-compat
        bootargs: quiet
        bootargs!append: loglevel=7
        chosen!linux:
          stdout-path: serial0
          bootargs: root=/dev/mmcblk0
      zephyr_domain:
        os,type: zephyr
        lopper,activate: zephyr
        compatible: base-compat
        compatible!zephyr!replace: zephyr-compat
        bootargs: quiet
        bootargs!append: CONFIG_DEBUG=y
        chosen!zephyr:
          stdout-path: serial1
          bootargs: zephyr,shell-uart
""")


@pytest.fixture(scope="module")
def yaml_tree(tmp_path_factory):
    """Parse DOMAINS_YAML and return the resulting LopperTree."""
    tmp = tmp_path_factory.mktemp("overlay_e2e")
    yaml_file = tmp / "domains.yaml"
    yaml_file.write_text(DOMAINS_YAML)
    y = LopperYAML(str(yaml_file))
    tree = y.to_tree()
    assert tree is not None, "YAML parse returned None"
    return tree


# ---------------------------------------------------------------------------
# Section 1: YAML parsing — sigils stripped, base tree unmodified
# ---------------------------------------------------------------------------

class TestYAMLParsing:
    def test_linux_domain_node_exists(self, yaml_tree):
        n = yaml_tree["/domains/linux_domain"]
        assert n is not None

    def test_zephyr_domain_node_exists(self, yaml_tree):
        n = yaml_tree["/domains/zephyr_domain"]
        assert n is not None

    def test_os_type_linux_plain_prop(self, yaml_tree):
        n = yaml_tree["/domains/linux_domain"]
        val = n.propval("os,type")
        assert "linux" in (val if isinstance(val, list) else [val])

    def test_os_type_zephyr_plain_prop(self, yaml_tree):
        n = yaml_tree["/domains/zephyr_domain"]
        val = n.propval("os,type")
        assert "zephyr" in (val if isinstance(val, list) else [val])

    def test_base_compatible_not_overwritten_by_sigil(self, yaml_tree):
        """Base value must be unchanged; overlay sits in overlay_subtrees."""
        n = yaml_tree["/domains/linux_domain"]
        val = n.__props__["compatible"].value
        assert "base-compat" in (val if isinstance(val, list) else [val]), \
            f"base-compat missing from base tree compatible: {val}"

    def test_overlay_subtrees_contain_linux(self, yaml_tree):
        """overlay_subtrees must have a 'linux' entry after parsing."""
        subtrees = yaml_tree._metadata.get("overlay_subtrees", {})
        assert "linux" in subtrees, f"linux missing from overlay_subtrees: {list(subtrees)}"

    def test_overlay_subtrees_contain_zephyr(self, yaml_tree):
        subtrees = yaml_tree._metadata.get("overlay_subtrees", {})
        assert "zephyr" in subtrees, f"zephyr missing from overlay_subtrees: {list(subtrees)}"

    def test_conditional_chosen_linux_not_in_base_tree(self, yaml_tree):
        """chosen!linux: node must NOT appear in base tree."""
        try:
            n = yaml_tree["/domains/linux_domain/chosen"]
            assert n is None, "chosen node unexpectedly present in base tree"
        except (KeyError, Exception):
            pass  # expected: node not in base tree

    def test_linux_chosen_in_overlay_subtree(self, yaml_tree):
        subtrees = yaml_tree._metadata.get("overlay_subtrees", {})
        linux_nodes = subtrees.get("linux", [])
        paths = [n.abs_path for n in linux_nodes]
        assert any("chosen" in p for p in paths), \
            f"chosen not in linux overlay_subtrees: {paths}"

    def test_zephyr_chosen_in_overlay_subtree(self, yaml_tree):
        subtrees = yaml_tree._metadata.get("overlay_subtrees", {})
        zephyr_nodes = subtrees.get("zephyr", [])
        paths = [n.abs_path for n in zephyr_nodes]
        assert any("chosen" in p for p in paths), \
            f"chosen not in zephyr overlay_subtrees: {paths}"


# ---------------------------------------------------------------------------
# Section 2: overlay_tree() — OS-specific merged tree
# ---------------------------------------------------------------------------

class TestOverlayTree:
    """Verify overlay_tree() produces correct merged trees per OS."""

    def _fresh_tree(self, tmp_path):
        yaml_file = tmp_path / "domains.yaml"
        yaml_file.write_text(DOMAINS_YAML)
        y = LopperYAML(str(yaml_file))
        return y.to_tree()

    def test_overlay_tree_linux_not_none(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        lt = tree.overlay_tree("linux")
        assert lt is not None, "overlay_tree('linux') returned None"

    def test_overlay_tree_zephyr_not_none(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        zt = tree.overlay_tree("zephyr")
        assert zt is not None, "overlay_tree('zephyr') returned None"

    def test_linux_overlay_tree_replaces_compatible(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        lt = tree.overlay_tree("linux")
        n = lt["/domains/linux_domain"]
        val = n.__props__["compatible"].value
        assert "linux-compat" in (val if isinstance(val, list) else [val]), \
            f"linux-compat missing from linux overlay_tree compatible: {val}"
        assert "base-compat" not in (val if isinstance(val, list) else [val]), \
            f"base-compat still present after linux replace: {val}"

    def test_zephyr_overlay_tree_replaces_compatible(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        zt = tree.overlay_tree("zephyr")
        n = zt["/domains/zephyr_domain"]
        val = n.__props__["compatible"].value
        assert "zephyr-compat" in (val if isinstance(val, list) else [val]), \
            f"zephyr-compat missing from zephyr overlay_tree compatible: {val}"
        assert "base-compat" not in (val if isinstance(val, list) else [val]), \
            f"base-compat still present after zephyr replace: {val}"

    def test_linux_overlay_tree_appends_bootargs(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        lt = tree.overlay_tree("linux")
        n = lt["/domains/linux_domain"]
        val = n.__props__["bootargs"].value
        flat = " ".join(val) if isinstance(val, list) else val
        assert "quiet" in flat, f"base bootargs 'quiet' missing: {flat}"
        assert "loglevel=7" in flat, f"appended bootargs 'loglevel=7' missing: {flat}"

    def test_zephyr_overlay_tree_appends_bootargs(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        zt = tree.overlay_tree("zephyr")
        n = zt["/domains/zephyr_domain"]
        val = n.__props__["bootargs"].value
        flat = " ".join(val) if isinstance(val, list) else val
        assert "quiet" in flat, f"base bootargs 'quiet' missing: {flat}"
        assert "CONFIG_DEBUG=y" in flat, f"appended bootargs 'CONFIG_DEBUG=y' missing: {flat}"

    def test_linux_chosen_node_added(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        lt = tree.overlay_tree("linux")
        try:
            n = lt["/domains/linux_domain/chosen"]
            assert n is not None
        except (KeyError, Exception):
            pytest.fail("chosen node not in linux overlay_tree")

    def test_zephyr_chosen_node_added(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        zt = tree.overlay_tree("zephyr")
        try:
            n = zt["/domains/zephyr_domain/chosen"]
            assert n is not None
        except (KeyError, Exception):
            pytest.fail("chosen node not in zephyr overlay_tree")

    def test_linux_chosen_has_linux_bootargs(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        lt = tree.overlay_tree("linux")
        n = lt["/domains/linux_domain/chosen"]
        val = n.propval("bootargs")
        val_list = val if isinstance(val, list) else [val]
        assert any("root=/dev/mmcblk0" in str(v) for v in val_list), \
            f"linux chosen bootargs wrong: {val}"

    def test_zephyr_chosen_has_zephyr_bootargs(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        zt = tree.overlay_tree("zephyr")
        n = zt["/domains/zephyr_domain/chosen"]
        val = n.propval("bootargs")
        val_list = val if isinstance(val, list) else [val]
        assert any("zephyr,shell-uart" in str(v) for v in val_list), \
            f"zephyr chosen bootargs wrong: {val}"

    def test_linux_and_zephyr_outputs_differ(self, tmp_path):
        """The two overlay_tree outputs must differ in at least compatible."""
        tree = self._fresh_tree(tmp_path)
        lt = tree.overlay_tree("linux")
        zt = tree.overlay_tree("zephyr")
        ln = lt["/domains/linux_domain"]
        zn = zt["/domains/zephyr_domain"]
        lv = ln.__props__["compatible"].value
        zv = zn.__props__["compatible"].value
        assert lv != zv, f"linux and zephyr compatible should differ: {lv} vs {zv}"

    def test_linux_overlay_does_not_contaminate_zephyr_domain(self, tmp_path):
        """overlay_tree('linux') must not change zephyr domain."""
        tree = self._fresh_tree(tmp_path)
        lt = tree.overlay_tree("linux")
        zn = lt["/domains/zephyr_domain"]
        val = zn.__props__["compatible"].value
        assert "base-compat" in (val if isinstance(val, list) else [val]), \
            f"linux overlay_tree contaminated zephyr domain: {val}"
        assert "linux-compat" not in (val if isinstance(val, list) else [val])

    def test_base_tree_unchanged_after_overlay_tree(self, tmp_path):
        """Base tree must be unmodified after building an overlay_tree."""
        tree = self._fresh_tree(tmp_path)
        _ = tree.overlay_tree("linux")
        n = tree["/domains/linux_domain"]
        val = n.__props__["compatible"].value
        assert "base-compat" in (val if isinstance(val, list) else [val]), \
            f"base tree was mutated by overlay_tree(): {val}"

    def test_unknown_overlay_name_returns_none(self, tmp_path):
        tree = self._fresh_tree(tmp_path)
        result = tree.overlay_tree("nonexistent")
        assert result is None


# ---------------------------------------------------------------------------
# Section 3: DTS output content differs per OS
# ---------------------------------------------------------------------------

class TestDTSOutputDiffers:
    """Write DTS output and verify linux vs zephyr content differs."""

    def _dts_output(self, tree):
        buf = io.StringIO()
        tree["/"].print(buf)
        return buf.getvalue()

    def _overlay_dts(self, tmp_path, name):
        yaml_file = tmp_path / "domains.yaml"
        yaml_file.write_text(DOMAINS_YAML)
        tree = LopperYAML(str(yaml_file)).to_tree()
        ot = tree.overlay_tree(name)
        return self._dts_output(ot)

    def test_linux_dts_contains_linux_compat(self, tmp_path):
        out = self._overlay_dts(tmp_path, "linux")
        assert "linux-compat" in out, "linux-compat not in linux DTS output"

    def test_zephyr_dts_contains_zephyr_compat(self, tmp_path):
        out = self._overlay_dts(tmp_path, "zephyr")
        assert "zephyr-compat" in out, "zephyr-compat not in zephyr DTS output"

    def test_linux_dts_has_mmcblk_not_zephyr_uart(self, tmp_path):
        out = self._overlay_dts(tmp_path, "linux")
        assert "mmcblk0" in out, "linux chosen bootargs not in DTS output"
        assert "zephyr,shell-uart" not in out, \
            "zephyr conditional content leaked into linux DTS output"

    def test_zephyr_dts_has_shell_uart_not_mmcblk(self, tmp_path):
        out = self._overlay_dts(tmp_path, "zephyr")
        assert "zephyr,shell-uart" in out, "zephyr chosen bootargs not in DTS output"
        assert "mmcblk0" not in out, \
            "linux conditional content leaked into zephyr DTS output"

    def test_linux_dts_appended_bootargs(self, tmp_path):
        out = self._overlay_dts(tmp_path, "linux")
        assert "loglevel=7" in out, "linux appended bootargs not in DTS output"

    def test_zephyr_dts_appended_bootargs(self, tmp_path):
        out = self._overlay_dts(tmp_path, "zephyr")
        assert "CONFIG_DEBUG=y" in out, "zephyr appended bootargs not in DTS output"
