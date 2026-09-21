"""Object-oriented Python implementation of a subset of the the Bbox local API"""

from cachetools import cached, TTLCache
from dataclasses import dataclass
from datetime import datetime
from dateutil.parser import isoparse
from requests import get
from typing import Any, Callable, Literal, TypeVar
from urllib.parse import urljoin, quote
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network, _BaseAddress, _BaseNetwork

# TODO: Add per-port stats

T = TypeVar('T')
def extract( d: dict, k: str, cb: Callable[[Any], T] ) -> T:
    if not isinstance(d, dict):
        raise TypeError('cannot extract %r from non-object value'%k)
    if k not in d:
        raise KeyError('%r is missing from object'%k)
    try:
        return cb(d[k])
    except BaseException as e:
        raise ValueError('failed to parse %r (%r)'%(k, d[k])) from e

class HTTPError( BaseException ):
    pass

@dataclass
class Bandwidth:
    bandwidth: int
    bytes: int
    packets: int

    @staticmethod
    def from_dict( value: dict ) -> Bandwidth:
        return Bandwidth(
            bandwidth = extract(value, 'bandwidth', int),
            bytes = extract(value, 'bytes', int),
            packets = extract(value, 'packets', int)
        )

@dataclass
class Version:
    version: tuple[int, ...]

    @staticmethod
    def from_dict( value: dict ) -> Version:
        return Version(version = extract(value, 'version', lambda v: tuple(int(it) for it in v.split('.'))))

@dataclass
class Date:
    date: datetime

    @staticmethod
    def from_dict( value: dict ) -> Date:
        return Date(date = extract(value, 'date', isoparse))

@dataclass
class VerDate( Version, Date ):
    @staticmethod
    def from_dict( value: dict ) -> VerDate:
        return VerDate(
            version = extract(value, 'version', lambda v: tuple(int(it) for it in v.split('.'))),
            date = extract(value, 'date', isoparse)
        )

@dataclass
class LinkStatus:
    state: Literal['Up', 'Down']
    type: str

    @staticmethod
    def from_dict( value: dict ) -> LinkStatus:
        return LinkStatus(
            state = extract(value, 'state', str), # TODO: Ensure part of enum (+ verify possible values) # pyright: ignore[reportArgumentType]
            type = extract(value, 'type', str),
        )

@dataclass
class WanBandwidth( Bandwidth ):
    packetserrors: int
    packetsdiscards: int
    occupation: int
    maxBandwidth: int
    contractualBandwidth: int

    @staticmethod
    def from_dict( value: dict ) -> WanBandwidth:
        return WanBandwidth(
            bandwidth = extract(value, 'bandwidth', int),
            bytes = extract(value, 'bytes', int),
            packets = extract(value, 'packets', int),
            packetserrors = extract(value, 'packetserrors', int),
            packetsdiscards = extract(value, 'packetsdiscards', int),
            occupation = extract(value, 'occupation', int),
            maxBandwidth = extract(value, 'maxBandwidth', int),
            contractualBandwidth = extract(value, 'contractualBandwidth', int),
        )

@dataclass
class WanStats:
    rx: WanBandwidth
    tx: WanBandwidth

    @staticmethod
    def from_dict( value: dict ) -> WanStats:
        return WanStats(
            rx = extract(value, 'rx', WanBandwidth.from_dict),
            tx = extract(value, 'tx', WanBandwidth.from_dict)
        )

@dataclass
class DeviceDisplayInfo:
    luminosity: int
    luminosity_extender: int
    state: str

    @staticmethod
    def from_dict( value: dict ) -> DeviceDisplayInfo:
        return DeviceDisplayInfo(
            luminosity = extract(value, 'luminosity', int),
            luminosity_extender = extract(value, 'luminosity_extender', int),
            state = extract(value, 'state', str)
        )

@dataclass
class DeviceUsingInfo:
    ipv4: bool
    ipv6: bool
    ftth: bool
    adsl: bool
    vdsl: bool

    @staticmethod
    def from_dict( value: dict ) -> DeviceUsingInfo:
        return DeviceUsingInfo(
            ipv4 = extract(value, 'ipv4', bool),
            ipv6 = extract(value, 'ipv6', bool),
            ftth = extract(value, 'ftth', bool),
            adsl = extract(value, 'adsl', bool),
            vdsl = extract(value, 'vdsl', bool)
        )

@dataclass
class DeviceInfo:
    now: datetime
    status: int
    numberofboots: int
    modelname: str
    modelclass: str
    optimisation: int
    user_configured: int
    display: DeviceDisplayInfo
    main: VerDate
    reco: VerDate
    running: VerDate
    spl: Version
    tpl: Version
    ldr1: Version
    ldr2: Version
    firstusedate: datetime
    uptime: int
    lastFactoryReset: int
    using: DeviceUsingInfo
    isCellularEnable: bool
    newihm: int
    newihmCdc: int

    @staticmethod
    def from_dict( value: dict ) -> DeviceInfo:
        return DeviceInfo(
            now = extract(value, 'now', isoparse),
            status = extract(value, 'status', int),
            numberofboots = extract(value, 'numberofboots', int),
            modelname = extract(value, 'modelname', str),
            modelclass = extract(value, 'modelclass', str),
            optimisation = extract(value, 'optimisation', int),
            user_configured = extract(value, 'user_configured', int),
            display = extract(value, 'display', DeviceDisplayInfo.from_dict),
            main = extract(value, 'main', VerDate.from_dict),
            reco = extract(value, 'reco', VerDate.from_dict),
            running = extract(value, 'running', VerDate.from_dict),
            spl = extract(value, 'spl', Version),
            tpl = extract(value, 'tpl', Version),
            ldr1 = extract(value, 'ldr1', Version),
            ldr2 = extract(value, 'ldr2', Version),
            firstusedate = extract(value, 'firstusedate', isoparse),
            uptime = extract(value, 'uptime', int),
            lastFactoryReset = extract(value, 'lastFactoryReset', int),
            using = extract(value, 'using', DeviceUsingInfo.from_dict),
            isCellularEnable = extract(value, 'isCellularEnable', bool),
            newihm = extract(value, 'newihm', int),
            newihmCdc = extract(value, 'newihmCdc', int)
        )

@dataclass
class WanInternetInfo:
    state: int

    @staticmethod
    def from_dict( value: dict ) -> WanInternetInfo:
        return WanInternetInfo(state = extract(value, 'state', int))

@dataclass
class WanInterfaceInfo:
    id: int
    default: int
    state: int

    @staticmethod
    def from_dict( value: dict ) -> WanInterfaceInfo:
        return WanInterfaceInfo(
            id = extract(value, 'id', int),
            default = extract(value, 'default', int),
            state = extract(value, 'state', int)
        )

@dataclass
class IpInfo:
    status: str
    valid: datetime
    preferred: datetime

    @staticmethod
    def from_dict( value: dict ) -> IpInfo:
        return IpInfo(
            status = extract(value, 'status', str),
            valid = extract(value, 'valid', isoparse),
            preferred = extract(value, 'preferred', isoparse),
        )

@dataclass
class BoundIp6AddressInfo( IpInfo ):
    ipaddress: IPv6Address
    status: str
    valid: datetime
    preferred: datetime

    @staticmethod
    def from_dict( value: dict ) -> BoundIp6AddressInfo:
        return BoundIp6AddressInfo(
            ipaddress = extract(value, 'ipaddress', IPv6Address),
            status = extract(value, 'status', str),
            valid = extract(value, 'valid', isoparse),
            preferred = extract(value, 'preferred', isoparse),
        )

@dataclass
class BoundIp6PrefixInfo( IpInfo ):
    prefix: IPv6Network
    status: str
    valid: datetime
    preferred: datetime

    @staticmethod
    def from_dict( value: dict ) -> BoundIp6PrefixInfo:
        return BoundIp6PrefixInfo(
            prefix = extract(value, 'prefix', IPv6Network),
            status = extract(value, 'status', str),
            valid = extract(value, 'valid', isoparse),
            preferred = extract(value, 'preferred', isoparse),
        )

@dataclass
class WanIP6AddressInfo( IpInfo ):
    ipaddress: IPv6Address

    @staticmethod
    def from_dict( value: dict ) -> WanIP6AddressInfo:
        return WanIP6AddressInfo(
            ipaddress = extract(value, 'ipaddress', IPv6Address),
            status = extract(value, 'status', str),
            valid = extract(value, 'valid', isoparse),
            preferred = extract(value, 'preferred', isoparse),
        )

@dataclass
class WanIp6PrefixInfo( IpInfo ):
    prefix: IPv6Network

    @staticmethod
    def from_dict( value: dict ) -> WanIp6PrefixInfo:
        return WanIp6PrefixInfo(
            prefix = extract(value, 'prefix', IPv6Network),
            status = extract(value, 'status', str),
            valid = extract(value, 'valid', isoparse),
            preferred = extract(value, 'preferred', isoparse),
        )

@dataclass
class WanIpInfo:
    address: IPv4Address
    cgnatenable: bool
    maptenable: bool
    state: Literal['Up', 'Down']
    gateway: _BaseAddress
    dnsservers: tuple[IPv4Address, ...]
    subnet: IPv4Network
    dnsserversv6: tuple[IPv6Address, ...]
    ip6state: Literal['Up', 'Down']
    ip6address: tuple[WanIP6AddressInfo, ...]
    ip6prefix: tuple[WanIp6PrefixInfo, ...]
    mac: str
    mtu: int

    @staticmethod
    def from_dict( value: dict ) -> WanIpInfo:
        return WanIpInfo(
            address = extract(value, 'address', IPv4Address),
            cgnatenable = extract(value, 'cgnatenable', bool),
            maptenable = extract(value, 'maptenable', bool),
            state = extract(value, 'state', str), # TODO: Ensure part of enum (+ verify possible values) # pyright: ignore[reportArgumentType]
            gateway = extract(value, 'gateway', ip_address),
            dnsservers = extract(value, 'dnsservers', lambda l: tuple(IPv4Address(it) for it in l.split(','))),
            subnet = extract(value, 'subnet', IPv4Network),
            dnsserversv6 = extract(value, 'dnsserversv6', lambda l: tuple(IPv6Address(it) for it in l.split(','))),
            ip6state = extract(value, 'ip6state', str), # TODO: Ensure part of enum (+ verify possible values) # pyright: ignore[reportArgumentType]
            ip6address = extract(value, 'ip6address', lambda l: tuple(WanIP6AddressInfo.from_dict(it) for it in l)),
            ip6prefix = extract(value, 'ip6prefix', lambda l: tuple(WanIp6PrefixInfo.from_dict(it) for it in l)),
            mac = extract(value, 'mac', str),
            mtu = extract(value, 'mtu', int),
        )

@dataclass
class WanInfo:
    internet: WanInternetInfo
    interface: WanInterfaceInfo
    ip: WanIpInfo
    link: LinkStatus

    @staticmethod
    def from_dict( value: dict ) -> WanInfo:
        return WanInfo(
            internet = extract(value, 'internet', WanInternetInfo.from_dict),
            interface = extract(value, 'interface', WanInterfaceInfo.from_dict),
            ip = extract(value, 'ip', WanIpInfo.from_dict),
            link = extract(value, 'link', LinkStatus.from_dict)
        )

@dataclass
class LanIpInfo:
    state: Literal['Up', 'Down']
    mtu: int
    ipaddress: IPv4Address
    ip6enable: bool
    ip6enableGlobal: bool
    ip6state: Literal['Up', 'Down']
    ip6address: tuple[BoundIp6AddressInfo, ...]
    ip6prefix: tuple[BoundIp6PrefixInfo, ...]
    netmask: IPv4Network
    mac: str
    hostname: str
    domain: str
    aliases: tuple[str, ...]

    @staticmethod
    def from_dict( value: dict ) -> LanIpInfo:
        return LanIpInfo(
            state = extract(value, 'state', str), # TODO: Ensure part of enum (+ verify possible values) # pyright: ignore[reportArgumentType]
            mtu = extract(value, 'mtu', int),
            ipaddress = extract(value, 'ipaddress', IPv4Address),
            ip6enable = extract(value, 'ip6enable', bool),
            ip6enableGlobal = extract(value, 'ip6enableGlobal', bool),
            ip6state = extract(value, 'ip6state', str), # TODO: Ensure part of enum (+ verify possible values) # pyright: ignore[reportArgumentType]
            ip6address = extract(value, 'ip6address', lambda l: tuple(BoundIp6AddressInfo.from_dict(it) for it in l)),
            ip6prefix = extract(value, 'ip6prefix', lambda l: tuple(BoundIp6PrefixInfo.from_dict(it) for it in l)),
            netmask = extract(value, 'netmask', IPv4Network),
            mac = extract(value, 'mac', str),
            hostname = extract(value, 'hostname', str),
            domain = extract(value, 'domain', str),
            aliases = extract(value, 'aliases', lambda l: tuple(l.split(',')))
        )

@dataclass
class LanPortInfo:
    id: int
    state: Literal['Up', 'Down']
    link_mode: str
    blocked: bool
    flickering: bool

    @staticmethod
    def from_dict( value: dict ) -> LanPortInfo:
        return LanPortInfo(
            id = extract(value, 'id', int),
            state = extract(value, 'state', str), # TODO: Ensure part of enum (+ verify possible values) # pyright: ignore[reportArgumentType]
            link_mode = extract(value, 'link_mode', str),
            blocked = extract(value, 'blocked', bool),
            flickering = extract(value, 'flickering', bool),
        )

@dataclass
class LanSwitchInfo:
    ports: tuple[LanPortInfo, ...]

    @staticmethod
    def from_dict( value: dict ) -> LanSwitchInfo:
        return LanSwitchInfo(ports = extract(value, 'ports', lambda l: tuple(LanPortInfo.from_dict(it) for it in l)))

@dataclass
class LanInfo:
    ip: LanIpInfo
    switch: LanSwitchInfo

    @staticmethod
    def from_dict( value: dict ) -> LanInfo:
        return LanInfo(
            ip = extract(value, 'ip', LanIpInfo.from_dict),
            switch = extract(value, 'switch', LanSwitchInfo.from_dict)
        )

@cached(TTLCache(10, 1))
def request( *path: str, at: tuple[str, ...]|None = None ):
    url = urljoin('http://192.168.1.254/api/v1/', '/'.join(quote(it, safe='') for it in path))
    res = get(url)
    if res.status_code != 200:
        raise HTTPError('Failed to fetch %r'%url)
    val = res.json()
    if not isinstance(val, list) or len(val) != 1:
        raise TypeError('Server replied with invalid data')
    val = val[0]
    for it in at or path:
        if not isinstance(val, dict) or it not in val:
            raise TypeError('Server replied with invalid data')
        val = val[it]
    return val

@cached(TTLCache(1, 60))
def get_wan_info() -> WanInfo:
    return WanInfo.from_dict(request('wan', 'ip', at=('wan',)))

@cached(TTLCache(1, 60))
def get_wan_stats() -> WanStats:
    return WanStats.from_dict(request('wan', 'ip', 'stats'))

@cached(TTLCache(1, 120))
def get_lan_info() -> LanInfo:
    return LanInfo.from_dict(request('lan', 'ip', at=('lan',)))

@cached(TTLCache(1, 5))
def get_device() -> DeviceInfo:
    return DeviceInfo.from_dict(request('device'))
