import typer
from pathlib import Path
from utils import leetcode as lc_fetch, ai as ai_gen, runner as test_runner, submit as submit_mod

app = typer.Typer(help="LeetCode local assistant CLI")

BASE_DIR = Path(__file__).parent.resolve()
PROBLEMS_DIR = BASE_DIR / "problems"
PROBLEMS_DIR.mkdir(exist_ok=True)

@app.command()
def pull(slug: str, force: bool = typer.Option(False, "--force-refresh", "-f", help="Force refresh from LeetCode (ignore cache)")):
    """Pull a LeetCode problem offline, generate tests via AI."""
    typer.echo(f"📥 Fetching problem: {slug}")
    # pass force flag to fetch_problem (uses cache by default)
    statement = lc_fetch.fetch_problem(slug, force=force)
    problem_dir = PROBLEMS_DIR / slug
    problem_dir.mkdir(parents=True, exist_ok=True)

    (problem_dir / "README.md").write_text(statement)
    solution = problem_dir / "solution.py"
    if not solution.exists():
        solution.write_text("# Write your solution in this file\nclass Solution:\n    pass\n")

    typer.echo("🤖 Generating tests via AI...")
    test_code = ai_gen.generate_tests(statement)
    (problem_dir / "test_solution.py").write_text(test_code)
    typer.echo(f"✅ Problem {slug} prepared at {problem_dir}")

@app.command()
def test(slug: str):
    """Run pytest for the given problem."""
    problem_dir = PROBLEMS_DIR / slug
    if not problem_dir.exists():
        typer.echo("Problem not found. Run `pull` first.", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"🧪 Running tests for {slug}")
    test_runner.run_tests(problem_dir)

@app.command()
def submit(slug: str):
    """Submit local solution to LeetCode (automation placeholder)."""
    problem_dir = PROBLEMS_DIR / slug
    sol = problem_dir / "solution.py"
    if not sol.exists():
        typer.echo("Solution not found. Edit solution.py first.", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"🚀 Submitting {slug} (automation)...")
    submit_mod.submit_solution(slug, sol)

if __name__ == "__main__":
    app()
    