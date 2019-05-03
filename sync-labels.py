#!/usr/bin/env python3

from github import Github
from github.GithubObject import NotSet
from github.Repository import Repository
from github.Label import Label
from github.GithubException import UnknownObjectException
from concurrent.futures import ThreadPoolExecutor, as_completed
import toml
import os
from dataclasses import dataclass
from typing import List, Optional, Union
import logging
import multiprocessing


@dataclass()
class Config:
    token: str
    source_repository: str
    target_repositories: List[str]


def sync_labels(config: Config):
    github_client = Github(config.token)

    source_labels = [*github_client.get_repo(
        config.source_repository, lazy=True).get_labels()]

    worker_count = len(config.target_repositories)
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(_sync_labels_to_repository,
                                   github_client, source_labels, repository) for repository in config.target_repositories]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exception:
                print(f'Error trying to sync labels: {exception}')


def _sync_labels_to_repository(github_client: Github, source_labels: List[Label], target_repository_name: str):
    repository = github_client.get_repo(target_repository_name, lazy=True)

    for source_label in source_labels:
        target_label = _get_label_by_name(repository, source_label.name)
        label_description = _get_label_description(source_label)

        if target_label is None:
            logging.info(
                f'Creating new label "{source_label.name}" in {target_repository_name}')
            repository.create_label(
                source_label.name, source_label.color, label_description)
        else:
            logging.info(
                f'Updating existing label "{source_label.name}" in {target_repository_name}')
            target_label.edit(source_label.name,
                              source_label.color, label_description)


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
