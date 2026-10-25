"""Build the static site and deploy it to a Hugging Face Space (static Spaces are free).

    hf auth login
    python scripts/deploy_space.py USER/SPACE_NAME [--public]

The Space is created private unless --public is given. Re-running updates it.
"""

from __future__ import annotations

import argparse

from huggingface_hub import HfApi

from build_web import DIST, main as build


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_id", help="e.g. abdufarag/ai-detector-check")
    parser.add_argument("--public", action="store_true", help="make the Space public")
    args = parser.parse_args()

    build()
    api = HfApi()
    url = api.create_repo(args.repo_id, repo_type="space", space_sdk="static",
                          private=not args.public, exist_ok=True)
    api.update_repo_settings(args.repo_id, repo_type="space", private=not args.public)
    api.upload_folder(repo_id=args.repo_id, repo_type="space", folder_path=str(DIST),
                      commit_message="Deploy static site", delete_patterns=["*"])
    print(f"Deployed {'public' if args.public else 'private'} Space: {url}")


if __name__ == "__main__":
    main()
