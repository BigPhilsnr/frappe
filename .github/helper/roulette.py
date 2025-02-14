import json
import os
import re
import shlex
import subprocess
import sys
import urllib.request


def get_files_list(pr_number, repo="frappe/frappe"):
	req = urllib.request.Request(f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files")
	res = urllib.request.urlopen(req)
	dump = json.loads(res.read().decode('utf8'))
	return [change["filename"] for change in dump]

def get_output(command, shell=True):
	print(command)
	command = shlex.split(command)
	return subprocess.check_output(command, shell=shell, encoding="utf8").strip()

def is_py(file):
	return file.endswith("py")

def is_ci(file):
	return ".github" in file

def is_frontend_code(file):
	return file.endswith((".css", ".scss", ".less", ".sass", ".styl", ".js", ".ts"))

def is_docs(file):
	regex = re.compile(r'\.(md|png|jpg|jpeg|csv)$|^.github|LICENSE')
	return bool(regex.search(file))


if __name__ == "__main__":
	files_list = sys.argv[1:]
	build_type = os.environ.get("TYPE")
	pr_number = os.environ.get("PR_NUMBER")
	repo = os.environ.get("REPO_NAME")

	if not files_list and pr_number:
		files_list = get_files_list(pr_number=pr_number, repo=repo)

	if not files_list:
		print("No files' changes detected. Build is shutting")
		sys.exit(0)

	ci_files_changed = any(f for f in files_list if is_ci(f))
	only_docs_changed = len(list(filter(is_docs, files_list))) == len(files_list)
	only_frontend_code_changed = len(list(filter(is_frontend_code, files_list))) == len(files_list)
	only_py_changed = len(list(filter(is_py, files_list))) == len(files_list)

	if ci_files_changed:
		print("CI related files were updated, running all build processes.")

	elif only_docs_changed:
		print("Only docs were updated, stopping build process.")
		sys.exit(0)

	elif only_frontend_code_changed and build_type == "server":
		print("Only Frontend code was updated; Stopping Python build process.")
		sys.exit(0)

	elif only_py_changed and build_type == "ui":
		print("Only Python code was updated, stopping Cypress build process.")
		sys.exit(0)

	os.system('echo "::set-output name=build::strawberry"')
