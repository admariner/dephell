# built-in
import asyncio

import pytest

# project
from dephell.constants import DEFAULT_WAREHOUSE
from dephell.controllers import DependencyMaker
from dephell.models import RootDependency, Auth
from dephell.repositories import WarehouseAPIRepo


loop = asyncio.get_event_loop()


@pytest.mark.allow_hosts()
def test_extra():
    repo = WarehouseAPIRepo(name='pypi', url=DEFAULT_WAREHOUSE)

    coroutine = repo.get_dependencies(name='requests', version='2.21.0')
    deps = loop.run_until_complete(asyncio.gather(coroutine))[0]
    deps = {dep.name: dep for dep in deps}
    assert 'chardet' in deps
    assert 'cryptography' not in deps
    assert 'win-inet-pton' not in deps

    coroutine = repo.get_dependencies(name='requests', version='2.21.0', extra='security')
    deps = loop.run_until_complete(asyncio.gather(coroutine))[0]
    deps = {dep.name: dep for dep in deps}
    assert 'chardet' not in deps
    assert 'win-inet-pton' not in deps
    assert 'cryptography' in deps


@pytest.mark.allow_hosts()
def test_info_from_files():
    repo = WarehouseAPIRepo(name='pypi', url=DEFAULT_WAREHOUSE)
    coroutine = repo.get_dependencies(name='m2r', version='0.2.1')
    deps = loop.run_until_complete(asyncio.gather(coroutine))[0]
    deps = {dep.name: dep for dep in deps}
    assert set(deps) == {'mistune', 'docutils'}


def test_get_releases(requests_mock, temp_cache, fixtures_path):
    url = 'https://pypi.org/pypi/'
    text = (fixtures_path / 'warehouse-api-response.json').read_text()
    requests_mock.get(url + 'dephell-shells/json', text=text)

    root = RootDependency()
    dep = DependencyMaker.from_requirement(source=root, req='dephell-shells')[0]
    repo = WarehouseAPIRepo(name='pypi', url=url)
    releases = repo.get_releases(dep=dep)

    assert requests_mock.call_count == 1
    assert len(releases) == 4


def test_get_releases_auth(requests_mock, temp_cache, fixtures_path):
    url = 'https://custom.pypi.org/pypi/'
    text = (fixtures_path / 'warehouse-api-response.json').read_text()
    requests_mock.get(url + 'dephell-shells/json', text=text)

    root = RootDependency()
    dep = DependencyMaker.from_requirement(source=root, req='dephell-shells')[0]
    repo = WarehouseAPIRepo(name='pypi', url=url, auth=Auth(
        hostname='custom.pypi.org',
        username='gram',
        password='test',
    ))
    releases = repo.get_releases(dep=dep)

    assert requests_mock.call_count == 1
    assert len(releases) == 4
    assert requests_mock.last_request.headers['Authorization'] == 'Basic Z3JhbTp0ZXN0'
