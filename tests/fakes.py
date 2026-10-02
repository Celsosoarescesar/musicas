"""Fakes leves para simular objetos do reapy nos testes, sem precisar do REAPER aberto."""


class FakeNote:
    def __init__(self, pitch, start=0.0, end=1.0, velocity=100):
        self.pitch = pitch
        self.start = start
        self.end = end
        self.velocity = velocity


class FakeSource:
    def __init__(self, filename):
        self.filename = filename


class FakeTake:
    def __init__(self, is_midi=True, source=None):
        self.is_midi = is_midi
        self.notes = []
        self.source = source

    def add_note(self, start, end, pitch, velocity=100, channel=0, unit="seconds"):
        note = FakeNote(pitch, start=start, end=end, velocity=velocity)
        self.notes.append(note)
        return note


class FakeItem:
    def __init__(self, start=0.0, end=1.0, track=None):
        self.start = start
        self.end = end
        self.active_take = FakeTake()
        self._track = track

    def delete(self):
        if self._track is not None and self in self._track.items:
            self._track.items.remove(self)


class FakeFXParam:
    def __init__(self, name, normalized=0.0):
        self.name = name
        self.normalized = normalized


class FakeFX:
    def __init__(self, name, param_names=(), is_enabled=True):
        self.name = name
        self.params = [FakeFXParam(param_name) for param_name in param_names]
        self.is_enabled = is_enabled

    def disable(self):
        self.is_enabled = False

    def enable(self):
        self.is_enabled = True


class FakeSend:
    def __init__(self, dest_track, volume=0.0):
        self.dest_track = dest_track
        self.volume = volume


class FakeTrack:
    def __init__(
        self,
        name,
        volume=1.0,
        pan=0.0,
        is_muted=False,
        is_solo=False,
        color=(0, 0, 0),
        depth=0,
    ):
        self.name = name
        self.volume = volume
        self.pan = pan
        self.is_muted = is_muted
        self.is_solo = is_solo
        self.color = color
        self.depth = depth
        self.fxs = []
        self.items = []
        self.sends = []
        self.is_selected = False
        self._info_values = {}

    @property
    def n_items(self):
        return len(self.items)

    @property
    def n_sends(self):
        return len(self.sends)

    def add_send(self, dest_track, volume=0.0):
        send = FakeSend(dest_track, volume=volume)
        self.sends.append(send)
        return send

    def get_info_value(self, param_name):
        return self._info_values.get(param_name, 0.0)

    def set_info_value(self, param_name, value):
        self._info_values[param_name] = value

    def make_only_selected_track(self):
        self.is_selected = True

    def add_fx(self, fx_name):
        fx = FakeFX(fx_name)
        self.fxs.append(fx)
        return fx

    def add_midi_item(self, start=0.0, end=1.0):
        item = FakeItem(start=start, end=end, track=self)
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
