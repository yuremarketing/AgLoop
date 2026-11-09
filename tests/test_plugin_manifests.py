import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(relpath):
    with open(os.path.join(REPO_ROOT, relpath), "r", encoding="utf-8") as f:
        return json.load(f)


def _pyproject_version():
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "r", encoding="utf-8") as f:
        content = f.read()
    return re.search(r'^version\s*=\s*"([^"]+)"', content, flags=re.MULTILINE).group(1)


def test_claude_plugin_json_has_required_fields():
    manifest = _load(".claude-plugin/plugin.json")
    assert manifest["name"] == "agloop"
    assert manifest["version"]
    assert manifest["description"]


def test_claude_marketplace_json_has_required_fields_and_matches_plugin():
    marketplace = _load(".claude-plugin/marketplace.json")
    assert marketplace["name"]
    assert marketplace["owner"]["name"]
    assert len(marketplace["plugins"]) >= 1

    plugin_json = _load(".claude-plugin/plugin.json")
    entry = marketplace["plugins"][0]
    assert entry["name"] == plugin_json["name"]
    assert entry["source"]


def test_claude_marketplace_source_points_at_repo_root():
    marketplace = _load(".claude-plugin/marketplace.json")
    entry = marketplace["plugins"][0]
    # "./" means the plugin.json lives at the marketplace root, same repo.
    assert entry["source"] == "./"
    assert os.path.isfile(os.path.join(REPO_ROOT, ".claude-plugin", "plugin.json"))


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
    claude_plugin = _load(".claude-plugin/plugin.json")
    gemini_extension = _load("gemini-extension.json")

    assert claude_plugin["version"] == pyproject_version
    assert gemini_extension["version"] == pyproject_version


# --- Issue #25: Claude Directory validator hygiene ----------------------------------


def test_session_start_hook_script_exists():
    assert os.path.isfile(os.path.join(REPO_ROOT, "scripts", "session_start_hook.py"))


def test_run_mcp_server_script_exists():
    assert os.path.isfile(os.path.join(REPO_ROOT, "scripts", "run_mcp_server.py"))


def test_claude_plugin_icon_exists_and_is_square_png():
    from PIL import Image

    icon_path = os.path.join(REPO_ROOT, ".claude-plugin", "icon.png")
    assert os.path.isfile(icon_path)
    with Image.open(icon_path) as img:
        assert img.format == "PNG"
        assert img.size[0] == img.size[1]
        assert 512 <= img.size[0] <= 2048


def test_hooks_json_points_at_script_file_not_inline_python():
    with open(os.path.join(REPO_ROOT, "hooks", "hooks.json"), "r", encoding="utf-8") as f:
        hooks = json.load(f)
    command = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert "-c" not in command.split()
    assert "|| true" not in command
    assert "scripts/session_start_hook.py" in command


def test_mcp_json_points_at_script_file_not_module_by_name():
    mcp = _load(".mcp.json")
    args = mcp["mcpServers"]["agloop"]["args"]
    assert args == ["scripts/run_mcp_server.py"]


def test_gemini_extension_still_uses_module_by_name():
    """Unlike .mcp.json, gemini-extension.json is intentionally left as -m
    core.mcp_server: the Gemini CLI supports module execution natively and
    this isn't a Claude Directory submission."""
    manifest = _load("gemini-extension.json")
    assert manifest["mcpServers"]["agloop"]["args"] == ["-m", "core.mcp_server"]
