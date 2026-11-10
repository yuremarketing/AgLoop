import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_ROOT = os.path.join(REPO_ROOT, "plugin")


def _load(relpath, base=REPO_ROOT):
    with open(os.path.join(base, relpath), "r", encoding="utf-8") as f:
        return json.load(f)


def _pyproject_version():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "r", encoding="utf-8") as f:
        content = f.read()
    return re.search(r'^version\s*=\s*"([^"]+)"', content, flags=re.MULTILINE).group(1)


def test_claude_plugin_json_has_required_fields():
    manifest = _load(".claude-plugin/plugin.json", base=PLUGIN_ROOT)
    assert manifest["name"] == "agloop"
    assert manifest["version"]
    assert manifest["description"]
    assert manifest["license"]


def test_claude_plugin_json_has_directory_links():
    # Claude Directory submission (Issue #28 follow-up): supportUrl and
    # privacyPolicyUrl are optional but were flagged as missing in the
    # listing review ("Links: 3 of 6 filled in"). termsOfServiceUrl is left
    # unset on purpose: there's no real ToS behind an MIT-licensed project.
    manifest = _load(".claude-plugin/plugin.json", base=PLUGIN_ROOT)
    assert manifest["supportUrl"] == "https://github.com/yuremarketing/AgLoop/issues"
    assert manifest["privacyPolicyUrl"].startswith("https://github.com/yuremarketing/AgLoop/blob/main/plugin/README.md")


def test_claude_plugin_json_has_display_name_and_keywords():
    # Listing review also flagged displayName as auto-filled from the GitHub
    # repo name ("Agloop", losing AgLoop's capitalization) and keywords unset.
    manifest = _load(".claude-plugin/plugin.json", base=PLUGIN_ROOT)
    assert manifest["displayName"] == "AgLoop"
    assert isinstance(manifest["keywords"], list) and len(manifest["keywords"]) >= 1


def test_claude_marketplace_json_has_required_fields_and_matches_plugin():
    marketplace = _load(".claude-plugin/marketplace.json")
    assert marketplace["name"]
    assert marketplace["owner"]["name"]
    assert len(marketplace["plugins"]) >= 1

    plugin_json = _load(".claude-plugin/plugin.json", base=PLUGIN_ROOT)
    entry = marketplace["plugins"][0]
    assert entry["name"] == plugin_json["name"]
    assert entry["source"]


def test_claude_marketplace_source_points_at_plugin_subfolder():
    marketplace = _load(".claude-plugin/marketplace.json")
    entry = marketplace["plugins"][0]
    # Issue #28: the distributed plugin lives in plugin/, not the repo root,
    # so third-party installers don't receive the War Room governance docs.
    assert entry["source"] == "./plugin"
    assert os.path.isfile(os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json"))


def test_gemini_extension_json_has_required_fields():
    manifest = _load("gemini-extension.json")
    assert manifest["name"] == "agloop"
    assert manifest["version"]
    assert manifest["description"]
    assert "agloop" in manifest["mcpServers"]
    assert manifest["mcpServers"]["agloop"]["command"] == "python3"
    assert manifest["mcpServers"]["agloop"]["args"] == ["-m", "core.mcp_server"]


def test_version_is_consistent_across_manifests_and_pyproject():
    pyproject_version = _pyproject_version()
    claude_plugin = _load(".claude-plugin/plugin.json", base=PLUGIN_ROOT)
    gemini_extension = _load("gemini-extension.json")

    assert claude_plugin["version"] == pyproject_version
    assert gemini_extension["version"] == pyproject_version


# --- Issue #25: Claude Directory validator hygiene ----------------------------------


def test_session_start_hook_script_exists():
    assert os.path.isfile(os.path.join(PLUGIN_ROOT, "scripts", "session_start_hook.py"))


def test_run_mcp_server_script_exists():
    assert os.path.isfile(os.path.join(PLUGIN_ROOT, "scripts", "run_mcp_server.py"))


def test_claude_plugin_icon_exists_and_is_square_png():
    # Read the PNG signature + IHDR chunk directly (width/height as big-endian
    # uint32 at fixed offsets) instead of depending on Pillow at test time —
    # it's only used to *generate* the icon, not a runtime/test dependency.
    icon_path = os.path.join(PLUGIN_ROOT, ".claude-plugin", "icon.png")
    assert os.path.isfile(icon_path)
    with open(icon_path, "rb") as f:
        header = f.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    assert header[12:16] == b"IHDR"
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    assert width == height
    assert 512 <= width <= 2048


def test_hooks_json_points_at_script_file_not_inline_python():
    with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json"), "r", encoding="utf-8") as f:
        hooks = json.load(f)
    hook = hooks["hooks"]["SessionStart"][0]["hooks"][0]
    # Issue #28 (Directory validator): the interpreter belongs in `command`
    # and the script path in `args`, not combined in a single command string.
    assert hook["command"] == "python3"
    args = hook["args"]
    assert "-c" not in args
    assert "|| true" not in " ".join(args)
    assert args[0] == "${CLAUDE_PLUGIN_ROOT}/scripts/session_start_hook.py"


def test_mcp_json_points_at_script_file_not_module_by_name():
    mcp = _load(".mcp.json", base=PLUGIN_ROOT)
    args = mcp["mcpServers"]["agloop"]["args"]
    # Directory validator (Issue #28 follow-up): write the file as
    # ${CLAUDE_PLUGIN_ROOT}/ and its path, same form already used in
    # plugin/hooks/hooks.json.
    assert args == ["${CLAUDE_PLUGIN_ROOT}/scripts/run_mcp_server.py"]


def test_gemini_extension_still_uses_module_by_name():
    """Unlike .mcp.json, gemini-extension.json is intentionally left as -m
    core.mcp_server: the Gemini CLI supports module execution natively and
    this isn't a Claude Directory submission."""
    manifest = _load("gemini-extension.json")
    assert manifest["mcpServers"]["agloop"]["args"] == ["-m", "core.mcp_server"]


# --- Issue #28: plugin/ subfolder restructuring --------------------------------------


def test_root_mcp_json_points_into_plugin_subfolder():
    """The repo root keeps its own .mcp.json so this dev repo's own Claude Code
    session (enabledMcpjsonServers in .claude/settings.local.json) keeps working,
    pointing at the relocated script inside plugin/."""
    mcp = _load(".mcp.json")
    args = mcp["mcpServers"]["agloop"]["args"]
    assert args == ["plugin/scripts/run_mcp_server.py"]


def test_plugin_scripts_do_not_reach_outside_plugin_folder():
    """Claude Directory blocks a component path that climbs above the plugin
    folder, so these scripts must import `core` as an installed package
    instead of walking up sys.path to the dev repo root."""
    for name in ("run_mcp_server.py", "session_start_hook.py"):
        with open(os.path.join(PLUGIN_ROOT, "scripts", name), "r", encoding="utf-8") as f:
            content = f.read()
        assert "sys.path.insert" not in content
        assert "dirname(dirname(" not in content


def test_plugin_readme_exists():
    readme_path = os.path.join(PLUGIN_ROOT, "README.md")
    assert os.path.isfile(readme_path)
    with open(readme_path, "r", encoding="utf-8") as f:
        text = f.read()
    assert len(text.split()) >= 40
