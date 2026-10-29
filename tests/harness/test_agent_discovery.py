import subprocess
import sys
import unittest
from pathlib import Path

class TestAgentDiscovery(unittest.TestCase):
    def test_validate_harness_script(self):
        base_dir = Path(__file__).parent.parent.parent
        script_path = base_dir / "scripts" / "harness" / "validate_harness.py"
        
        self.assertTrue(script_path.is_file(), "validate_harness.py script not found")
        
        res = subprocess.run(
            [sys.executable, str(script_path), "--strict"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.assertEqual(res.returncode, 0, f"validate_harness.py script failed with code {res.returncode}. Stderr: {res.stderr}")

    def test_agent_models_are_valid(self):
        base_dir = Path(__file__).parent.parent.parent
        agents_dir = base_dir / ".agents" / "agents"
        valid_models = {"inherit", "pro", "flash", "flash_lite"}
        expected_agents = [
            "ralph-orchestrator",
            "terukirdo-plan",
            "agy-worker",
            "first-reviewer",
            "tech-expert",
            "universal-final-controller",
            "final-approach-control",
        ]
        for agent in expected_agents:
            agent_file = agents_dir / agent / "agent.md"
            self.assertTrue(agent_file.is_file(), f"Missing agent file: {agent_file}")
            content = agent_file.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---"), f"{agent} missing YAML frontmatter delimiter")
            parts = content.split("---", 2)
            self.assertGreaterEqual(len(parts), 3, f"{agent} missing closing YAML frontmatter delimiter")
            frontmatter = parts[1]
            model = None
            for line in frontmatter.splitlines():
                if line.strip().startswith("model:"):
                    model = line.split(":", 1)[1].strip().strip('"').strip("'")
                    break
            self.assertIsNotNone(model, f"{agent} missing model in frontmatter")
            self.assertIn(model, valid_models, f"{agent} model '{model}' not in {valid_models}")

    def test_agent_tools_permissions_contract(self):
        base_dir = Path(__file__).parent.parent.parent
        agents_dir = base_dir / ".agents" / "agents"
        write_tools = {"write_file", "edit_file", "notebook_edit"}
        expected_agents = [
            "ralph-orchestrator",
            "terukirdo-plan",
            "agy-worker",
            "first-reviewer",
            "tech-expert",
            "universal-final-controller",
            "final-approach-control",
        ]
        for agent in expected_agents:
            agent_file = agents_dir / agent / "agent.md"
            content = agent_file.read_text(encoding="utf-8")
            frontmatter = content.split("---", 2)[1]
            tools = []
            in_tools = False
            for line in frontmatter.splitlines():
                stripped = line.strip()
                if stripped.startswith("tools:"):
                    in_tools = True
                    continue
                if in_tools:
                    if stripped.startswith("- "):
                        tools.append(stripped[2:].strip())
                    elif stripped and not line.startswith(" ") and not line.startswith("\t"):
                        in_tools = False
            self.assertTrue(len(tools) > 0, f"{agent} must declare explicit tools list in frontmatter")
            tool_set = set(tools)
            if agent == "agy-worker":
                self.assertTrue(
                    {"write_file", "edit_file", "run_command"}.issubset(tool_set),
                    f"agy-worker missing write/shell tools: {tool_set}",
                )
            else:
                self.assertTrue(
                    tool_set.isdisjoint(write_tools),
                    f"Read-only agent {agent} must not have write tools: {tool_set & write_tools}",
                )

if __name__ == "__main__":
    unittest.main()
