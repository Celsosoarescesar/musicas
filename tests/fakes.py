"""Fakes leves para simular objetos do reapy nos testes, sem precisar do REAPER aberto."""


class FakeNote:
    def __init__(self, pitch, start=0.0, end=1.0, velocity=100):
        self.pitch = pitch
        self.start = start
        self.end = end
        self.velocity = velocity


class FakeTake:
    def __init__(self, is_midi=True):
        self.is_midi = is_midi
        self.notes = []

    def add_note(self, start, end, pitch, velocity=100, channel=0, unit="seconds"):
        note = FakeNote(pitch, start=start, end=end, velocity=velocity)
        self.notes.append(note)
        return note


class FakeItem:
    def __init__(self, start=0.0, end=1.0):
        self.start = start
        self.end = end
        self.active_take = FakeTake()


class FakeFXParam:
    def __init__(self, name, normalized=0.0):
        self.name = name
        self.normalized = normalized


class FakeFX:
    def __init__(self, name, param_names=()):
        self.name = name
        self.params = [FakeFXParam(param_name) for param_name in param_names]


class FakeTrack:
    def __init__(self, name, volume=1.0, pan=0.0, is_muted=False, is_solo=False):
        self.name = name
        self.volume = volume
        self.pan = pan
        self.is_muted = is_muted
        self.is_solo = is_solo
        self.fxs = []
        self.items = []

    def add_fx(self, fx_name):
        fx = FakeFX(fx_name)
        self.fxs.append(fx)
        return fx

    def add_midi_item(self, start=0.0, end=1.0):
        item = FakeItem(start=start, end=end)
        self.items.append(item)
        return item


class FakeProject:
    def __init__(self, tracks=None):
        self.tracks = list(tracks or [])
        self.cursor_position = 0.0
        self.master_track = FakeTrack("MASTER")
        self._info_strings = {}

    @property
    def n_tracks(self):
        return len(self.tracks)

    def add_track(self, index, name):
        track = FakeTrack(name)
        self.tracks.insert(index, track)
        return track

    def set_info_string(self, param_name, value):
        self._info_strings[param_name] = value

    def get_info_string(self, param_name):
        return self._info_strings.get(param_name, "")
