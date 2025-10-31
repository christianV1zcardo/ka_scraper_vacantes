from types import ModuleType
import sys


def _create_module(name: str) -> ModuleType:
    module = ModuleType(name)
    sys.modules[name] = module
    return module


def ensure_selenium_stub() -> None:
    if "selenium" in sys.modules:
        return

    selenium = _create_module("selenium")
    webdriver = _create_module("selenium.webdriver")
    selenium.webdriver = webdriver  # type: ignore[attr-defined]

    def dummy_firefox(*_args, **_kwargs):
        return None

    webdriver.Firefox = dummy_firefox  # type: ignore[attr-defined]

    firefox_pkg = _create_module("selenium.webdriver.firefox")
    webdriver.firefox = firefox_pkg  # type: ignore[attr-defined]

    options_module = _create_module("selenium.webdriver.firefox.options")
    firefox_pkg.options = options_module  # type: ignore[attr-defined]

    class DummyOptions:
        def __init__(self) -> None:
            self.arguments = []

        def add_argument(self, argument: str) -> None:
            self.arguments.append(argument)

    options_module.Options = DummyOptions  # type: ignore[attr-defined]

    common_pkg = _create_module("selenium.webdriver.common")
    webdriver.common = common_pkg  # type: ignore[attr-defined]

    by_module = _create_module("selenium.webdriver.common.by")
    common_pkg.by = by_module  # type: ignore[attr-defined]

    class DummyBy:
        ID = "id"
        CSS_SELECTOR = "css selector"
        TAG_NAME = "tag name"
        XPATH = "xpath"

    by_module.By = DummyBy  # type: ignore[attr-defined]

    keys_module = _create_module("selenium.webdriver.common.keys")
    common_pkg.keys = keys_module  # type: ignore[attr-defined]

    class DummyKeys:
        RETURN = "RETURN"

    keys_module.Keys = DummyKeys  # type: ignore[attr-defined]

    support_pkg = _create_module("selenium.webdriver.support")
    webdriver.support = support_pkg  # type: ignore[attr-defined]

    expected_module = _create_module("selenium.webdriver.support.expected_conditions")
    support_pkg.expected_conditions = expected_module  # type: ignore[attr-defined]

    def presence_of_element_located(locator):
        return locator

    expected_module.presence_of_element_located = presence_of_element_located  # type: ignore[attr-defined]

    ui_module = _create_module("selenium.webdriver.support.ui")
    support_pkg.ui = ui_module  # type: ignore[attr-defined]

    class DummyWebDriverWait:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def until(self, condition):  # type: ignore[no-untyped-def]
            return condition

    ui_module.WebDriverWait = DummyWebDriverWait  # type: ignore[attr-defined]

    remote_pkg = _create_module("selenium.webdriver.remote")
    webdriver.remote = remote_pkg  # type: ignore[attr-defined]

    remote_webdriver_module = _create_module("selenium.webdriver.remote.webdriver")
    remote_pkg.webdriver = remote_webdriver_module  # type: ignore[attr-defined]

    class DummyRemoteWebDriver:
        def quit(self) -> None:  # pragma: no cover - stub
            pass

    remote_webdriver_module.WebDriver = DummyRemoteWebDriver  # type: ignore[attr-defined]
