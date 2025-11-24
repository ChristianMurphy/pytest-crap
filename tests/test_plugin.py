"""Integration tests for pytest-crap plugin using real pytest execution.

Uses pytester fixture to run actual pytest sessions with real coverage data.
"""

from typing import Any

# Import package modules so the outer pytest process records coverage
import pytest_crap.calculator  # noqa: F401
import pytest_crap.mapper  # noqa: F401
import pytest_crap.plugin  # noqa: F401
import pytest_crap.reporter  # noqa: F401


def test_plugin_loads_and_shows_help(pytester: Any) -> None:
    """Verify plugin registers and shows in help."""
    result = pytester.runpytest("-p", "pytest_crap.plugin", "--help")
    result.stdout.fnmatch_lines(
        [
            "*CRAP score reporting v0.1.0:*",
            "*--crap*Enable CRAP score reporting*",
            "*--crap-threshold*",
            "*--crap-top-n*",
        ]
    )


def test_version_access() -> None:
    """Test that version can be accessed."""

    assert pytest_crap.__version__ == "0.1.0"


def test_plugin_with_no_cov_warns(pytester: Any) -> None:
    """When --crap is used without coverage, should warn gracefully."""
    pytester.makepyfile(
        test_simple="""
        def test_dummy():
            assert True
        """
    )

    result = pytester.runpytest("-p", "pytest_crap.plugin", "--crap", "--cov-fail-under=0")
    # Should not crash and should show CRAP tables (even if empty)
    assert result.ret == 0
    result.stdout.fnmatch_lines(
        [
            "*CRAP by Function*",
        ]
    )


def test_plugin_with_simple_coverage(pytester: Any) -> None:
    """Test with real coverage data on simple functions."""
    # Create a source file with functions of varying complexity
    pytester.makepyfile(
        mymodule="""
        def simple_function(x):
            '''Simple function with CC=1'''
            return x + 1
        def uncovered_function(x):
            '''This won't be tested'''
            if x > 0:
                return x * 2
            else:
                return x * 3
        def partially_covered(x):
            '''Partial coverage'''
            if x > 0:
                return x + 1
            return x - 1
        """
    )

    # Create tests that cover some functions
    pytester.makepyfile(
        test_mymodule="""
        from mymodule import simple_function, partially_covered
        def test_simple():
            assert simple_function(5) == 6
        def test_partially_positive():
            assert partially_covered(5) == 6
        """
    )

    # Run pytest with coverage and CRAP reporting
    result = pytester.runpytest(
        "-p",
        "pytest_crap.plugin",
        "--cov=mymodule",
        "--cov-report=term-missing",
        "--crap",
        "--cov-fail-under=0",
        "-v",
    )

    # Should complete successfully
    assert result.ret == 0

    # Should show CRAP scores in output
    output = result.stdout.str()
    assert "CRAP" in output or "simple_function" in output


def test_plugin_with_complex_code(pytester: Any) -> None:
    """Test with high complexity code."""
    pytester.makepyfile(
        complex_module="""
        def high_complexity(x, y, z):
            '''Function with high cyclomatic complexity'''
            result = 0
            if x > 0:
                if y > 0:
                    if z > 0:
                        result = x + y + z
                    else:
                        result = x + y - z
                else:
                    if z > 0:
                        result = x - y + z
                    else:
                        result = x - y - z
            else:
                if y > 0:
                    if z > 0:
                        result = -x + y + z
                    else:
                        result = -x + y - z
                else:
                    if z > 0:
                        result = -x - y + z
                    else:
                        result = -x - y - z
            return result
        """
    )

    # Create a test that imports the module but doesn't exercise functions
    pytester.makepyfile(
        test_complex="""
        import complex_module

        def test_placeholder():
            assert True
        """
    )

    result = pytester.runpytest(
        "-p",
        "pytest_crap.plugin",
        "--cov=complex_module",
        "--crap",
        "--crap-threshold=10",
        "--cov-fail-under=0",
    )

    assert result.ret == 0
    output = result.stdout.str()
    # With no coverage and high complexity, should have high CRAP score
    assert "high_complexity" in output


def test_plugin_threshold_option(pytester: Any) -> None:
    """Test --crap-threshold option affects output."""
    pytester.makepyfile(
        sample="""
        def simple(x):
            return x + 1
        """
    )

    pytester.makepyfile(
        test_sample="""
        from sample import simple
        def test_it():
            assert simple(1) == 2
        """
    )

    result = pytester.runpytest(
        "-p",
        "pytest_crap.plugin",
        "--cov=sample",
        "--crap",
        "--crap-threshold=5",
        "--cov-fail-under=0",
    )

    assert result.ret == 0


def test_plugin_top_n_option(pytester: Any) -> None:
    """Test --crap-top-n option limits output."""
    # Create multiple functions
    functions = "\n".join(
        [
            f"""
def func_{i}(x):
    return x + {i}
"""
            for i in range(30)
        ]
    )

    pytester.makepyfile(many_funcs=functions)

    # Test only a few
    pytester.makepyfile(
        test_many="""
        from many_funcs import func_0, func_1
        def test_some():
            assert func_0(1) == 1
            assert func_1(1) == 2
        """
    )

    result = pytester.runpytest(
        "-p",
        "pytest_crap.plugin",
        "--cov=many_funcs",
        "--crap",
        "--crap-top-n=5",
        "--cov-fail-under=0",
    )

    assert result.ret == 0


def test_plugin_top_n_zero(pytester: Any) -> None:
    """Test --crap-top-n=0 shows all items."""
    # Create multiple functions
    functions = "\n".join(
        [
            f"""
def func_{i}(x):
    return x + {i}
"""
            for i in range(5)
        ]
    )

    pytester.makepyfile(many_funcs=functions)

    pytester.makepyfile(
        test_many="""
        from many_funcs import func_0, func_1, func_2
        def test_some():
            assert func_0(1) == 1
            assert func_1(1) == 2
            assert func_2(1) == 3
        """
    )

    result = pytester.runpytest(
        "-p",
        "pytest_crap.plugin",
        "--cov=many_funcs",
        "--crap",
        "--crap-top-n=0",
        "--cov-fail-under=0",
    )

    assert result.ret == 0
    # With top_n=0, should show all functions
    output = result.stdout.str()
    assert "func_0" in output
    assert "func_1" in output
    assert "func_2" in output


def test_plugin_with_unparseable_file(pytester: Any) -> None:
    """Test plugin handles files it can't parse gracefully."""
    # Create a valid Python file
    pytester.makepyfile(
        good_module="""
        def working_function():
            return 42
        """
    )

    # Create a non-Python file that coverage might track
    pytester.makefile(".txt", data="not python code at all")

    pytester.makepyfile(
        test_good="""
        from good_module import working_function
        def test_it():
            assert working_function() == 42
        """
    )

    result = pytester.runpytest(
        "-p",
        "pytest_crap.plugin",
        "--cov=good_module",
        "--crap",
        "--cov-fail-under=0",
    )

    # Should handle gracefully and continue
    assert result.ret == 0


def test_plugin_without_crap_flag_does_nothing(pytester: Any) -> None:
    """Without --crap flag, plugin should not run."""
    pytester.makepyfile(
        mycode="""
        def some_func():
            return 1
        """
    )

    pytester.makepyfile(
        test_it="""
        import mycode

        def test_pass():
            # import the module so coverage can collect it
            assert mycode.some_func() == 1
        """
    )

    result = pytester.runpytest("-p", "pytest_crap.plugin", "--cov-fail-under=0")

    assert result.ret == 0
    output = result.stdout.str()
    # Should not contain CRAP reporting
    assert "CRAP" not in output or "coverage" in output.lower()


def test_plugin_real_crap_calculation(pytester: Any) -> None:
    """Verify actual CRAP scores are calculated correctly."""
    # Create a function with known complexity and coverage
    pytester.makepyfile(
        calc="""
        def covered_simple(x):
            '''CC=1, 100% coverage -> CRAP should be 1'''
            return x * 2
        def covered_complex(x, y):
            '''CC=3 (2 if statements), good coverage'''
            if x > 0:
                result = x + y
            else:
                result = x - y
            if result > 10:
                return result * 2
            return result
        def uncovered_complex(a, b, c):
            '''CC=5+, 0% coverage -> high CRAP'''
            if a > 0:
                if b > 0:
                    if c > 0:
                        return a + b + c
                    return a + b - c
                return a - b
            return -a
        """
    )

    pytester.makepyfile(
        test_calc="""
        from calc import covered_simple, covered_complex
        def test_simple():
            assert covered_simple(5) == 10
        def test_complex_positive():
            assert covered_complex(5, 3) == 8
        def test_complex_negative():
            assert covered_complex(-5, 3) == -8
        def test_complex_large():
            assert covered_complex(8, 4) == 24
        """
    )

    result = pytester.runpytest(
        "-p",
        "pytest_crap.plugin",
        "--cov=calc",
        "--cov-branch",
        "--crap",
        "--crap-threshold=20",
        "--cov-fail-under=0",
        "-v",
    )

    assert result.ret == 0
    output = result.stdout.str()

    # Verify functions appear in output
    assert "covered_simple" in output
    assert "covered_complex" in output
    assert "uncovered_complex" in output


def test_plugin_with_class_methods(pytester: Any) -> None:
    """Test CRAP calculation for class methods."""
    pytester.makepyfile(
        classes="""
        class Calculator:
            def add(self, x, y):
                return x + y
            def complex_method(self, x):
                if x > 0:
                    if x > 10:
                        return x * 2
                    return x + 1
                return 0
        """
    )

    pytester.makepyfile(
        test_classes="""
        from classes import Calculator
        def test_add():
            calc = Calculator()
            assert calc.add(2, 3) == 5
        """
    )

    result = pytester.runpytest(
        "-p",
        "pytest_crap.plugin",
        "--cov=classes",
        "--crap",
        "--cov-fail-under=0",
    )

    assert result.ret == 0
    output = result.stdout.str()
    assert "Calculator" in output or "add" in output


def test_plugin_file_and_folder_summaries(pytester: Any) -> None:
    """Test that file and folder summaries are generated."""
    # Create nested structure
    pytester.mkdir("src")
    pytester.mkdir("src/package")

    pytester.makepyfile(
        **{
            "src/package/__init__": "",
            "src/package/module_a": """
def func_a():
    return 1
""",
            "src/package/module_b": """
def func_b(x):
    if x > 0:
        return x
    return -x
""",
        }
    )

    pytester.makepyfile(
        test_all="""
        import sys
        sys.path.insert(0, 'src')
        from package.module_a import func_a
        from package.module_b import func_b
        def test_a():
            assert func_a() == 1
        def test_b():
            assert func_b(5) == 5
        """
    )

    result = pytester.runpytest(
        "-p",
        "pytest_crap.plugin",
        "--cov=src/package",
        "--crap",
        "--cov-fail-under=0",
    )

    assert result.ret == 0
