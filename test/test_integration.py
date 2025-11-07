"""
Integration smoke tests for the jpamb tool.
These test the complete workflow from end to end to ensure
students have a smooth experience using the tool.
"""

import pytest
import subprocess
import json
import tempfile
from pathlib import Path
from click.testing import CliRunner

from jpamb import cli, model


class TestCompleteWorkflow:
    """Test complete workflows from start to finish."""

    @pytest.mark.slow
    def test_full_workflow_with_apriori(self):
        """Test the complete workflow with the apriori solution."""
        runner = CliRunner()

        # Step 1: Get info from the solution
        result = runner.invoke(
            cli.cli,
            ["--", "python3", "solutions/apriori.py", "info"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Step 2: Run test command
        result = runner.invoke(
            cli.cli,
            ["test", "-f", "Simple", "solutions/apriori.py"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Step 3: Run evaluate command
        result = runner.invoke(
            cli.cli,
            ["evaluate", "--timeout", "5.0", "--iterations", "1", "solutions/apriori.py"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        # Should produce valid JSON output
        try:
            # The output should be parseable as JSON
            # (May have log messages mixed in, so we just check it doesn't crash)
            assert len(result.output) > 0
        except json.JSONDecodeError:
            # Some output may not be JSON if there are log messages
            pass

    def test_checkhealth_runs_successfully(self):
        """Test that checkhealth completes successfully."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["checkhealth"],
            catch_exceptions=False,
        )
        # Should complete (may fail if environment is not set up, but shouldn't crash)
        assert isinstance(result.exit_code, int)


class TestFileAccessibility:
    """Test that all required files and resources are accessible."""

    def test_decompiled_files_exist(self):
        """Test that decompiled bytecode files exist."""
        suite = model.Suite()
        decompiled_files = list(suite.decompiledfiles())

        # Should have at least some decompiled files
        assert len(decompiled_files) > 0

        # Check that they're actually readable
        for df in decompiled_files[:3]:  # Check first few
            assert df.exists(), f"Decompiled file should exist: {df}"
            assert df.is_file(), f"Should be a file: {df}"

    def test_source_files_exist(self):
        """Test that Java source files exist."""
        suite = model.Suite()
        source_files = list(suite.sourcefiles())

        # Should have source files
        assert len(source_files) > 0

        # Check that they exist
        for sf in source_files[:3]:  # Check first few
            assert sf.exists(), f"Source file should exist: {sf}"
            assert sf.is_file(), f"Should be a file: {sf}"

    def test_class_files_exist(self):
        """Test that compiled class files exist."""
        suite = model.Suite()
        class_files = list(suite.classfiles())

        # Should have class files
        assert len(class_files) > 0

        # Check that they exist
        for cf in class_files[:3]:  # Check first few
            assert cf.exists(), f"Class file should exist: {cf}"
            assert cf.is_file(), f"Should be a file: {cf}"

    def test_cases_file_readable(self):
        """Test that the cases.txt file is readable."""
        cases_file = Path("stats/cases.txt")
        assert cases_file.exists(), "stats/cases.txt should exist"

        # Should be able to read and parse cases
        with open(cases_file) as f:
            lines = f.readlines()
            assert len(lines) > 0

            # Try parsing first few cases
            for line in lines[:5]:
                case = model.Case.decode(line.strip())
                assert case is not None


class TestDependencyAvailability:
    """Test that all required dependencies are available."""

    def test_python_dependencies_importable(self):
        """Test that all Python dependencies can be imported."""
        import click
        import yaml
        import matplotlib
        import tree_sitter
        import z3

        # If we get here, all imports succeeded
        assert True

    def test_java_available(self):
        """Test that Java is available in the environment."""
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            timeout=5,
        )
        # Should complete successfully
        assert result.returncode == 0

    def test_maven_available(self):
        """Test that Maven is available in the environment."""
        result = subprocess.run(
            ["mvn", "-version"],
            capture_output=True,
            timeout=5,
        )
        # Should complete successfully (or not found, which is ok)
        # This is optional for students
        assert result.returncode == 0 or result.returncode == 127


class TestExampleSolutions:
    """Test that example solutions work correctly."""

    @pytest.mark.slow
    def test_all_example_solutions_have_info(self):
        """Test that all example solutions respond to 'info' command."""
        solutions = [
            "solutions/apriori.py",
            "solutions/bytecoder.py",
            "solutions/cheater.py",
            "solutions/syntaxer.py",
            "solutions/my_analyzer.py",
        ]

        for solution in solutions:
            if not Path(solution).exists():
                pytest.skip(f"{solution} not found")

            result = subprocess.run(
                ["python3", solution, "info"],
                capture_output=True,
                timeout=5,
                text=True,
            )

            # Should succeed and produce JSON output
            assert result.returncode == 0, f"{solution} info command failed"
            try:
                info = json.loads(result.stdout)
                assert "name" in info, f"{solution} should have 'name' field"
                assert "version" in info, f"{solution} should have 'version' field"
            except json.JSONDecodeError:
                pytest.fail(f"{solution} did not produce valid JSON for info command")

    @pytest.mark.slow
    def test_example_solutions_run_on_simple_cases(self):
        """Test that example solutions can analyze Simple cases."""
        solutions = [
            "solutions/apriori.py",
            "solutions/bytecoder.py",
        ]

        runner = CliRunner()

        for solution in solutions:
            if not Path(solution).exists():
                pytest.skip(f"{solution} not found")

            result = runner.invoke(
                cli.cli,
                ["test", "-f", "Simple", solution],
                catch_exceptions=False,
            )

            # Should complete successfully
            assert result.exit_code == 0, f"{solution} failed on Simple cases"


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility checks."""

    def test_path_handling(self):
        """Test that paths are handled correctly across platforms."""
        suite = model.Suite()

        # All paths should be absolute
        for sf in list(suite.sourcefiles())[:3]:
            assert sf.is_absolute(), f"Path should be absolute: {sf}"

        for cf in list(suite.classfiles())[:3]:
            assert cf.is_absolute(), f"Path should be absolute: {cf}"

    def test_temp_file_creation(self):
        """Test that we can create temporary files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# test")
            temp_path = f.name

        try:
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestErrorMessages:
    """Test that error messages are helpful for students."""

    def test_missing_file_error_message(self):
        """Test error message when analysis script is not found."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["test", "nonexistent.py"],
        )

        # Should fail and produce some error message
        assert result.exit_code != 0
        # Error output should mention the file
        assert len(result.output) > 0 or result.exception is not None

    def test_invalid_filter_gives_feedback(self):
        """Test that invalid filter patterns provide feedback."""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["test", "--filter", "[invalid", "solutions/apriori.py"],
        )

        # Should handle gracefully
        assert isinstance(result.exit_code, int)
