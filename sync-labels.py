#!/usr/bin/env python3

from github import Github
from github.GithubObject import NotSet
from github.Repository import Repository
from github.Label import Label
from github.GithubException import UnknownObjectException
import toml
import os
from dataclasses import dataclass
from typing import List, Optional, Union
import logging

@dataclass()
class Config:
    token: str
    source_repository: str
    target_repositories: List[str]


def sync_labels(config: Config):
    g = Github(config.token)

    source_labels = g.get_repo(
        config.source_repository, lazy=True).get_labels()

    for repository_name in config.target_repositories:
        repository = g.get_repo(repository_name, lazy=True)

        logging.info(f'Syncing labels to {repository_name}')

        for source_label in source_labels:
            target_label = _get_label_by_name(repository, source_label.name)
            label_description = _get_label_description(source_label)

            if target_label is None:
                logging.info(f'Creating new label "{source_label.name}" in {repository_name}')
                repository.create_label(source_label.name, source_label.color, label_description)
            else:
                logging.info(f'Updating existing label "{source_label.name}" in {repository_name}')
                target_label.edit(source_label.name, source_label.color, label_description)


def _get_label_description(label: Label) -> Union[str, type(NotSet)]:
    if label.description is None:
        return NotSet
    else:
        return label.description


def _get_label_by_name(repository: Repository, label: str) -> Optional[Label]:
    try:
        return repository.get_label(label)
    except UnknownObjectException:
        return None


def _get_config() -> Config:
    config_file = os.path.join(os.path.dirname(__file__), 'config.toml')
    config = toml.load(config_file)
    return Config(token=config['token'],
                  source_repository=config['source_repository'],
                  target_repositories=config['target_repositories'])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    _config = _get_config()
    sync_labels(_config)
