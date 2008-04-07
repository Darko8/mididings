# -*- coding: utf-8 -*-
#
# mididings
#
# Copyright (C) 2008  Dominic Sacré  <dominic.sacre@gmx.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import _mididings
import misc
import units


_config = {
    'client_name':      'mididings',
    'in_ports':         1,
    'out_ports':        1,
    'data_offset':      1,
    'octave_offset':    2,
}

def config(**kwargs):
    for k in kwargs:
        if k not in _config:
            raise TypeError('unknown config variable: %s' % k)
        _config[k] = kwargs[k]


class Patch(_mididings.Patch):
    def __init__(self, p):
        _mididings.Patch.__init__(self)

        i = Patch.Module(Patch.Input())
        o = Patch.Module(Patch.Output())

        r = self.build(p)

        # attach all inputs
        for c in r[0]:
            i.attach(c)
        # attach all outputs
        for c in r[1]:
            c.attach(o)

        self.set_start(i)

    # recursively connects all units in p
    # returns the lists of inputs and outputs of p
    def build(self, p):
        if isinstance(p, units._Chain):
            # build both items
            a = self.build(p.items[0])
            b = self.build(p.items[1])
            # connect all of a's outputs to all of b's inputs
            for x in a[1]:
                for y in b[0]:
                    x.attach(y)
            # return a's inputs and b's outputs
            return a[0], b[1]
        elif isinstance(p, list):
            # build all items, return all inputs and outputs
            inp, outp = [], []
            for m in p:
                r = self.build(m)
                inp += r[0]
                outp += r[1]
            return inp, outp
        elif isinstance(p, dict):
            return self.build([ units.Filter(t) >> w for t, w in p.items() ])
        elif isinstance(p, units._Unit):
            # single unit is both input and output
            m = Patch.Module(p)
            return [m], [m]
        else:
            # whoops...
            raise TypeError()


class Setup(_mididings.Setup):
    def __init__(self, patches, control, pre, post):
        in_ports = _config['in_ports']
        out_ports = _config['out_ports']

        in_portnames = _mididings.string_vector()
        out_portnames = _mididings.string_vector()

        if not misc.issequence(in_ports):
            in_ports = [ 'in_' + str(n + _config['data_offset']) for n in range(in_ports) ]
        # fill vector with input port names
        for i in in_ports:
            in_portnames.push_back(i)

        if not misc.issequence(out_ports):
            out_ports = [ 'out_' + str(n + _config['data_offset']) for n in range(out_ports) ]
        # fill vector with output port names
        for i in out_ports:
            out_portnames.push_back(i)

        _mididings.Setup.__init__(self, '', _config['client_name'], in_portnames, out_portnames)

        for i, p in patches.items():
            if isinstance(p, tuple):
                init_patch, patch = Patch(p[0]), Patch(p[1])
            else:
                init_patch, patch = None, Patch(p)
            self.add_patch(i - _config['data_offset'], patch, init_patch)

        ctrl = Patch(control) if control else None
        pre_patch = Patch(pre) if pre else None
        post_patch = Patch(post) if post else None
        self.set_processing(ctrl, pre_patch, post_patch)

        import event
        self.switch_patch(0, event.MidiEvent())

    def print_switch_patch(self, n, found):
        if found:
            print "switching to patch: %d" % (n + _config['data_offset'])
        else:
            print "no such patch: %d" % (n + _config['data_offset'])


def run(patch):
    run_patches({ _config['data_offset']: patch }, None, None, None)

def run_patches(patches, control=None, pre=None, post=None):
    s = Setup(patches, control, pre, post)
    try:
        s.run()
    except KeyboardInterrupt:
        return


def test_run(patch, events):
    return test_run_patches({ _config['data_offset']: patch }, events)

def test_run_patches(patches, events):
    s = Setup(patches, None, None, None)
    r = []
    if not misc.issequence(events):
        events = [events]
    for ev in events:
        r += s.process(ev)[:]
    return r
