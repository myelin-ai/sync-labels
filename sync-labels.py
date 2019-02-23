#!/usr/bin/env python3

from github import Github, GithubObject
from github.GithubException import UnknownObjectException
import toml
import os


def sync_labels():
    config = _get_config()
    token = _get_gh_token()

    g = Github(token)

    source_labels = g.get_repo(
        config['source_repository'], lazy=True).get_labels()

    for repository_name in config['target_repositories']:
        repository = g.get_repo(repository_name, lazy=True)

        for source_label in source_labels:
            try:
                label = repository.get_label(source_label.name)
            except UnknownObjectException:
                label = None

            source_label_description = GithubObject.NotSet if source_label.description is None else source_label.description

            if label is None:
                repository.create_label(
                    source_label.name, source_label.color, source_label_description)
            else:
                label.edit(source_label.name, source_label.color,
                           source_label_description)


def _get_config():
    config_file = os.path.join(os.path.dirname(__file__), 'config.toml')
    return toml.load(config_file)


def _get_gh_token():
    return os.environ['GH_TOKEN']


if __name__ == '__main__':
    sync_labels()
