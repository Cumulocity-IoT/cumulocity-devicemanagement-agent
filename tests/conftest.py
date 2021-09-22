import pytest

def pytest_addoption(parser):
    parser.addoption("--serial", action="store")
    parser.addoption("--url", action="store")
    parser.addoption("--tenant", action="store")
    parser.addoption("--username", action="store")
    parser.addoption("--password", action="store")
  
@pytest.fixture(scope='session')
def options(request):
  options = {
    'serial': request.config.option.serial,
    'url': request.config.option.url,
    'tenant': request.config.option.tenant,
    'username': request.config.option.username,
    'password': request.config.option.password
  }
  if not all(options.values()):
    pytest.skip('all options should be provided')
  return options

