"""Windows Core Audio for the mic-display PC app: list devices, read and set volume and mute, switch the default
device. Pure comtypes, no other dependency.

Interfaces and GUIDs: Microsoft's Windows SDK headers mmdeviceapi.h, endpointvolume.h, functiondiscoverykeys_devpkey.h.
Switching the default device uses the undocumented IPolicyConfig interface that Windows' own Sound control panel
uses (no public API exists). Its layout (Windows 7 and later, still current on Windows 11) is taken from
EarTrumpet, the open-source Windows volume mixer: https://github.com/File-New-Project/EarTrumpet
(EarTrumpet/Interop/MMDeviceAPI/IPolicyConfig.cs and the AudioPolicyConfigFactory it ships with).

Every call must run on a thread that has called comtypes.CoInitialize(); the app keeps all of it on one thread.
"""
import ctypes
from ctypes import HRESULT, POINTER, Structure, Union, byref, c_float, c_uint, c_ulonglong, c_ushort, c_void_p, c_wchar_p
from ctypes.wintypes import BOOL, DWORD, LPCWSTR, LPWSTR, UINT

import comtypes
from comtypes import CLSCTX_ALL, COMMETHOD, GUID, IUnknown

# EDataFlow, ERole, DEVICE_STATE
RENDER, CAPTURE = 0, 1
CONSOLE, MULTIMEDIA, COMMUNICATIONS = 0, 1, 2
DEVICE_STATE_ACTIVE = 1


class PROPERTYKEY(Structure):
    _fields_ = [("fmtid", GUID), ("pid", DWORD)]


class _PVU(Union):
    _fields_ = [("pwszVal", c_wchar_p), ("ulVal", c_uint), ("pad", c_ulonglong * 2)]


class PROPVARIANT(Structure):
    _fields_ = [("vt", c_ushort), ("r1", c_ushort), ("r2", c_ushort), ("r3", c_ushort), ("u", _PVU)]


VT_LPWSTR = 31
_ole32 = ctypes.OleDLL("ole32")
_ole32.PropVariantClear.argtypes = [POINTER(PROPVARIANT)]
_ole32.CoTaskMemFree.argtypes = [c_void_p]


def _pkey(fmtid, pid):
    k = PROPERTYKEY()
    k.fmtid = GUID(fmtid)
    k.pid = pid
    return k


PKEY_Device_FriendlyName = _pkey("{a45c254e-df1c-4efd-8020-67d146a850e0}", 14)       # "Microphone (Yeti Stereo Microphone)"
PKEY_Device_DeviceDesc = _pkey("{a45c254e-df1c-4efd-8020-67d146a850e0}", 2)          # "Microphone"
PKEY_DeviceInterface_FriendlyName = _pkey("{026e516e-b814-414b-83cd-856d6fef4822}", 2)  # "Yeti Stereo Microphone"


class IPropertyStore(IUnknown):
    _iid_ = GUID("{886d8eeb-8cf2-4446-8d02-cdba1dbdcf99}")
    _methods_ = [
        COMMETHOD([], HRESULT, "GetCount", (["out"], POINTER(DWORD), "cProps")),
        COMMETHOD([], HRESULT, "GetAt", (["in"], DWORD, "iProp"), (["out"], POINTER(PROPERTYKEY), "pkey")),
        COMMETHOD([], HRESULT, "GetValue", (["in"], POINTER(PROPERTYKEY), "key"), (["in"], POINTER(PROPVARIANT), "pv")),
        COMMETHOD([], HRESULT, "SetValue", (["in"], POINTER(PROPERTYKEY), "key"), (["in"], POINTER(PROPVARIANT), "pv")),
        COMMETHOD([], HRESULT, "Commit"),
    ]


class IMMDevice(IUnknown):
    _iid_ = GUID("{D666063F-1587-4E43-81F1-B948E807363F}")
    _methods_ = [
        COMMETHOD([], HRESULT, "Activate", (["in"], POINTER(GUID), "iid"), (["in"], DWORD, "dwClsCtx"),
                  (["in"], c_void_p, "pActivationParams"), (["out"], POINTER(POINTER(IUnknown)), "ppInterface")),
        COMMETHOD([], HRESULT, "OpenPropertyStore", (["in"], DWORD, "stgmAccess"),
                  (["out"], POINTER(POINTER(IPropertyStore)), "ppProperties")),
        COMMETHOD([], HRESULT, "GetId", (["out"], POINTER(LPWSTR), "ppstrId")),
        COMMETHOD([], HRESULT, "GetState", (["out"], POINTER(DWORD), "pdwState")),
    ]


class IMMDeviceCollection(IUnknown):
    _iid_ = GUID("{0BD7A1BE-7A1A-44DB-8397-CC5392387B5E}")
    _methods_ = [
        COMMETHOD([], HRESULT, "GetCount", (["out"], POINTER(UINT), "pcDevices")),
        COMMETHOD([], HRESULT, "Item", (["in"], UINT, "nDevice"), (["out"], POINTER(POINTER(IMMDevice)), "ppDevice")),
    ]


class IMMDeviceEnumerator(IUnknown):
    _iid_ = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
    _methods_ = [
        COMMETHOD([], HRESULT, "EnumAudioEndpoints", (["in"], DWORD, "dataFlow"), (["in"], DWORD, "dwStateMask"),
                  (["out"], POINTER(POINTER(IMMDeviceCollection)), "ppDevices")),
        COMMETHOD([], HRESULT, "GetDefaultAudioEndpoint", (["in"], DWORD, "dataFlow"), (["in"], DWORD, "role"),
                  (["out"], POINTER(POINTER(IMMDevice)), "ppEndpoint")),
        COMMETHOD([], HRESULT, "GetDevice", (["in"], LPCWSTR, "pwstrId"), (["out"], POINTER(POINTER(IMMDevice)), "ppDevice")),
        COMMETHOD([], HRESULT, "RegisterEndpointNotificationCallback", (["in"], c_void_p, "pClient")),
        COMMETHOD([], HRESULT, "UnregisterEndpointNotificationCallback", (["in"], c_void_p, "pClient")),
    ]


class IAudioEndpointVolume(IUnknown):
    _iid_ = GUID("{5CDF2C82-841E-4546-9722-0CF74078229A}")
    _methods_ = [
        COMMETHOD([], HRESULT, "RegisterControlChangeNotify", (["in"], c_void_p, "pNotify")),
        COMMETHOD([], HRESULT, "UnregisterControlChangeNotify", (["in"], c_void_p, "pNotify")),
        COMMETHOD([], HRESULT, "GetChannelCount", (["out"], POINTER(UINT), "pnChannelCount")),
        COMMETHOD([], HRESULT, "SetMasterVolumeLevel", (["in"], c_float, "fLevelDB"), (["in"], POINTER(GUID), "pguidEventContext")),
        COMMETHOD([], HRESULT, "SetMasterVolumeLevelScalar", (["in"], c_float, "fLevel"), (["in"], POINTER(GUID), "pguidEventContext")),
        COMMETHOD([], HRESULT, "GetMasterVolumeLevel", (["out"], POINTER(c_float), "pfLevelDB")),
        COMMETHOD([], HRESULT, "GetMasterVolumeLevelScalar", (["out"], POINTER(c_float), "pfLevel")),
        COMMETHOD([], HRESULT, "SetChannelVolumeLevel", (["in"], UINT, "nChannel"), (["in"], c_float, "fLevelDB"),
                  (["in"], POINTER(GUID), "pguidEventContext")),
        COMMETHOD([], HRESULT, "SetChannelVolumeLevelScalar", (["in"], UINT, "nChannel"), (["in"], c_float, "fLevel"),
                  (["in"], POINTER(GUID), "pguidEventContext")),
        COMMETHOD([], HRESULT, "GetChannelVolumeLevel", (["in"], UINT, "nChannel"), (["out"], POINTER(c_float), "pfLevelDB")),
        COMMETHOD([], HRESULT, "GetChannelVolumeLevelScalar", (["in"], UINT, "nChannel"), (["out"], POINTER(c_float), "pfLevel")),
        COMMETHOD([], HRESULT, "SetMute", (["in"], BOOL, "bMute"), (["in"], POINTER(GUID), "pguidEventContext")),
        COMMETHOD([], HRESULT, "GetMute", (["out"], POINTER(BOOL), "pbMute")),
    ]


class IPolicyConfig(IUnknown):
    """Undocumented; vtable order as in EarTrumpet's IPolicyConfig.cs (see the module docstring)."""
    _iid_ = GUID("{f8679f50-850a-41cf-9c72-430f290290c8}")
    _methods_ = [
        COMMETHOD([], HRESULT, "GetMixFormat", (["in"], LPCWSTR, "id"), (["in"], c_void_p, "ppFormat")),
        COMMETHOD([], HRESULT, "GetDeviceFormat", (["in"], LPCWSTR, "id"), (["in"], BOOL, "bDefault"), (["in"], c_void_p, "ppFormat")),
        COMMETHOD([], HRESULT, "ResetDeviceFormat", (["in"], LPCWSTR, "id")),
        COMMETHOD([], HRESULT, "SetDeviceFormat", (["in"], LPCWSTR, "id"), (["in"], c_void_p, "pEndpointFormat"), (["in"], c_void_p, "mixFormat")),
        COMMETHOD([], HRESULT, "GetProcessingPeriod", (["in"], LPCWSTR, "id"), (["in"], BOOL, "bDefault"),
                  (["in"], c_void_p, "pmftDefaultPeriod"), (["in"], c_void_p, "pmftMinimumPeriod")),
        COMMETHOD([], HRESULT, "SetProcessingPeriod", (["in"], LPCWSTR, "id"), (["in"], c_void_p, "pmftPeriod")),
        COMMETHOD([], HRESULT, "GetShareMode", (["in"], LPCWSTR, "id"), (["in"], c_void_p, "pMode")),
        COMMETHOD([], HRESULT, "SetShareMode", (["in"], LPCWSTR, "id"), (["in"], c_void_p, "mode")),
        COMMETHOD([], HRESULT, "GetPropertyValue", (["in"], LPCWSTR, "id"), (["in"], BOOL, "bFxStore"),
                  (["in"], c_void_p, "key"), (["in"], c_void_p, "pv")),
        COMMETHOD([], HRESULT, "SetPropertyValue", (["in"], LPCWSTR, "id"), (["in"], BOOL, "bFxStore"),
                  (["in"], c_void_p, "key"), (["in"], c_void_p, "pv")),
        COMMETHOD([], HRESULT, "SetDefaultEndpoint", (["in"], LPCWSTR, "id"), (["in"], DWORD, "role")),
        COMMETHOD([], HRESULT, "SetEndpointVisibility", (["in"], LPCWSTR, "id"), (["in"], BOOL, "bVisible")),
    ]


CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
CLSID_PolicyConfigClient = GUID("{870af99c-171d-4f9e-af0d-e63df40c2bc9}")


def _prop(store, key):
    pv = PROPVARIANT()
    try:
        store.GetValue(byref(key), byref(pv))
        return pv.u.pwszVal if pv.vt == VT_LPWSTR else ""
    except comtypes.COMError:
        return ""
    finally:
        _ole32.PropVariantClear(byref(pv))


class Device:
    __slots__ = ("id", "friendly", "desc", "adapter")

    def __init__(self, id_, friendly, desc, adapter):
        self.id, self.friendly, self.desc, self.adapter = id_, friendly, desc, adapter

    def __repr__(self):
        return f"Device({self.friendly!r})"


class CoreAudio:
    """One instance per COM-initialised thread."""

    def __init__(self):
        self.en = comtypes.CoCreateInstance(CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, CLSCTX_ALL)
        self._policy = None

    def _device_info(self, dev):
        store = dev.OpenPropertyStore(0)   # STGM_READ
        return Device(dev.GetId(), _prop(store, PKEY_Device_FriendlyName), _prop(store, PKEY_Device_DeviceDesc),
                      _prop(store, PKEY_DeviceInterface_FriendlyName))

    def devices(self, flow):
        """Active endpoints of one direction, sorted by friendly name so the order is stable."""
        col = self.en.EnumAudioEndpoints(flow, DEVICE_STATE_ACTIVE)
        out = [self._device_info(col.Item(i)) for i in range(col.GetCount())]
        return sorted(out, key=lambda d: (d.friendly.lower(), d.id))

    def default_id(self, flow, role=CONSOLE):
        try:
            return self.en.GetDefaultAudioEndpoint(flow, role).GetId()
        except comtypes.COMError:   # no device of that kind
            return None

    def _volume(self, dev_id):
        dev = self.en.GetDevice(dev_id)
        return dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None).QueryInterface(IAudioEndpointVolume)

    def get_volume(self, dev_id):
        """(scalar 0..1, muted bool) of an endpoint."""
        v = self._volume(dev_id)
        return float(v.GetMasterVolumeLevelScalar()), bool(v.GetMute())

    def set_volume(self, dev_id, scalar):
        self._volume(dev_id).SetMasterVolumeLevelScalar(max(0.0, min(1.0, float(scalar))), None)

    def set_mute(self, dev_id, mute):
        self._volume(dev_id).SetMute(bool(mute), None)

    def set_default(self, dev_id, roles=(CONSOLE, MULTIMEDIA, COMMUNICATIONS)):
        if self._policy is None:
            self._policy = comtypes.CoCreateInstance(CLSID_PolicyConfigClient, IPolicyConfig, CLSCTX_ALL)
        for r in roles:
            self._policy.SetDefaultEndpoint(dev_id, r)


def snapshot(ca=None):
    """Everything the app can change, for a test to record and restore: default device per flow and role,
    volume scalar and mute of every active endpoint."""
    ca = ca or CoreAudio()
    snap = {"defaults": {}, "endpoints": {}}
    for flow, fname in ((RENDER, "render"), (CAPTURE, "capture")):
        for role, rname in ((CONSOLE, "console"), (MULTIMEDIA, "multimedia"), (COMMUNICATIONS, "communications")):
            snap["defaults"][f"{fname}.{rname}"] = ca.default_id(flow, role)
        for d in ca.devices(flow):
            vol, mute = ca.get_volume(d.id)
            snap["endpoints"][d.id] = {"flow": fname, "name": d.friendly, "volume": vol, "mute": mute}
    return snap


def restore(snap, ca=None):
    ca = ca or CoreAudio()
    for key, dev_id in snap["defaults"].items():
        if dev_id:
            role = {"console": CONSOLE, "multimedia": MULTIMEDIA, "communications": COMMUNICATIONS}[key.split(".")[1]]
            ca.set_default(dev_id, (role,))
    for dev_id, e in snap["endpoints"].items():
        try:
            ca.set_volume(dev_id, e["volume"])
            ca.set_mute(dev_id, e["mute"])
        except comtypes.COMError:
            pass   # unplugged since


if __name__ == "__main__":   # print the current state: python pcapp/core_audio.py
    import json
    comtypes.CoInitialize()
    print(json.dumps(snapshot(), indent=1))
