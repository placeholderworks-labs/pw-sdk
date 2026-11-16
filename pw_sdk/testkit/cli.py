import argparse
import sys
from pathlib import Path

from pw_sdk.schema import write_schemas
from pw_sdk.testkit.runner import check_directory
from pw_sdk.testkit.scaffold import scaffold


def _check(args) -> int:
    results = check_directory(Path(args.directory), args.adapter, args.update)
    if not results:
        print(f"no fixtures found in {args.directory}")
        return 1
    failed = [r for r in results if not r.passed]
    for result in results:
        print(f"{'PASS' if result.passed else 'FAIL'}  {result.name}")
        for problem in result.problems:
            print("      " + problem.replace("\n", "\n      "))
    print(f"{len(results) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


def _schema(args) -> int:
    for path in write_schemas(Path(args.out)):
        print(path)
    return 0


def _new(args) -> int:
    target = scaffold(args.slug, Path(args.parent))
    print(f"created {target}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pw-adapter")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="run adapters over fixtures and compare with expected output")
    check.add_argument("directory")
    check.add_argument("--adapter", help="entry point name or module:Class; default is the folder name")
    check.add_argument("--update", action="store_true", help="write the actual output as the expected output")
    check.set_defaults(run=_check)
    schema = commands.add_parser("schema", help="write the JSON Schemas of the canonical models")
    schema.add_argument("--out", default="schema")
    schema.set_defaults(run=_schema)
    new = commands.add_parser("new", help="create a new client adapter repo")
    new.add_argument("slug")
    new.add_argument("--parent", default=".")
    new.set_defaults(run=_new)
    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
