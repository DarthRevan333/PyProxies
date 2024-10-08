import requests
from os.path import exists
from os import remove

from .proxy import FetchedProxy, RankedProxies
from .utils import load_request_args, resolve_resource_path
from .exceptions import InvalidJSONResponse, InvalidResponseFormat


def delete_saved_free_proxies(resolved_path = resolve_resource_path("./saved_free_proxies.json")):
    remove(resolved_path)


def fetch_free_proxies(source_url: str = "https://api.proxyscrape.com/v3/free-proxy-list/get",
                       alt_params: dict[str, str] = None, alt_headers: dict[str, str] = None, n: int = 20,
                       ssl_support_required: bool = True, scheme: str = "socks4"):
    params, headers = load_request_args(
        alt_headers=alt_headers, alt_params=alt_params,
        ssl_support_required=ssl_support_required, scheme=scheme
    )

    try:
        response: dict = requests.get(source_url, params=params, headers=headers).json()["proxies"]
    except requests.JSONDecodeError:
        raise InvalidResponseFormat("Response was not a valid JSON response")
    except KeyError:
        raise InvalidJSONResponse("JSON response didn't contain \"proxies\" key")

    found_proxies: list[FetchedProxy] = sorted([
        FetchedProxy(ip=proxy["proxy"], protocol=proxy["protocol"], average_timeout=proxy["average_timeout"])
        for proxy in response
        if proxy.get("proxy") and proxy.get("protocol") and proxy.get("alive") and proxy.get("average_timeout")
    ], key=lambda proxy: proxy.average_timeout)

    return RankedProxies(found_proxies[:n])


def load_proxies_list(force_load: bool = False, n: int = 20, accept_insecure_proxies: bool = False) -> RankedProxies:
    """
    :param n: Number of proxies to consider.
    :param force_load: Whether to force a new series of requests to fetch new data
    :param accept_insecure_proxies: Whether to accept insecure proxies.
        If set to True only socks5 supporting proxies with SSL support are fetched.
        Otherwise, all schemes and SSL capabilities are accepted.
        Setting this to False may cause very few or no proxies at all to be found,
        though if proxies are found they are the most reliable free proxies.
    :return: A RankedProxies object holding all fetched/saved data ranked by quickest average response times
    """
    return RankedProxies.load() if exists(resolve_resource_path("./saved_free_proxies.json")) and not force_load \
        else fetch_free_proxies(
            n=n,
            ssl_support_required=not accept_insecure_proxies,
            scheme="all" if accept_insecure_proxies else "socks5"
        )


def main(accept_insecure_proxies: bool = False):
    n = 20
    pl = load_proxies_list(force_load=True, accept_insecure_proxies=accept_insecure_proxies)
    print(f"Found {pl.count} proxies.")
    print(f"Saved data to {resolve_resource_path('./saved_free_proxies.json')}")
    print(f"Best {n} proxies:\n")
    print("\n".join([f"{p.protocol}://{p.ip}" for p in pl.get_n_best(n)]))


if __name__ == '__main__':
    main()
