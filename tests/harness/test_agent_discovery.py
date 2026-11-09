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
            "legion-commander",
            "legion-worker",
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
            "legion-commander",
            "legion-worker",
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
            if agent in ("agy-worker", "legion-worker"):
                self.assertTrue(
                    {"write_file", "edit_file", "run_command"}.issubset(tool_set),
                    f"{agent} missing write/shell tools: {tool_set}",
                )
            else:
                self.assertTrue(
                    tool_set.isdisjoint(write_tools),
                    f"Read-only agent {agent} must not have write tools: {tool_set & write_tools}",
                )

    def test_dual_brain_operational_contracts_present(self):
        base_dir = Path(__file__).parent.parent.parent
        agents_dir = base_dir / ".agents" / "agents"

        # 1. first-reviewer and tech-expert contain 4-Element Defect Contract and No Finding Quota
        for agent in ("first-reviewer", "tech-expert"):
            content = (agents_dir / agent / "agent.md").read_text(encoding="utf-8")
            self.assertIn(
                "4-Element Defect Contract",
                content,
                f"{agent} missing 4-Element Defect Contract rule",
            )
            self.assertIn(
                "No Finding Quota",
                content,
                f"{agent} missing No Finding Quota rule",
            )

        # 2. ralph-orchestrator and legion-commander contain send_message subagent reuse rules
        for agent in ("ralph-orchestrator", "legion-commander"):
            content = (agents_dir / agent / "agent.md").read_text(encoding="utf-8")
            self.assertIn(
                "send_message",
                content,
                f"{agent} missing send_message in subagent reuse rules",
            )
            self.assertIn(
                "Subagent Handle Reuse",
                content,
                f"{agent} missing Subagent Handle Reuse section",
            )

        # 3. universal-final-controller and final-approach-control contain Baseline Test Integrity rule
        for agent in ("universal-final-controller", "final-approach-control"):
            content = (agents_dir / agent / "agent.md").read_text(encoding="utf-8")
            self.assertIn(
                "Baseline Test Integrity",
                content,
                f"{agent} missing Baseline Test Integrity rule",
            )

        # 4. MEMORY.md contains ## Archived Decisions
        memory_file = base_dir / "MEMORY.md"
        self.assertTrue(memory_file.is_file(), "MEMORY.md not found")
        memory_content = memory_file.read_text(encoding="utf-8")
        self.assertIn(
            "## Archived Decisions",
            memory_content,
            "MEMORY.md missing ## Archived Decisions section",
        )

if __name__ == "__main__":
    unittest.main()
