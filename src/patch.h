/*
 * mididings
 *
 * Copyright (C) 2007  Dominic Sacré  <dominic.sacre@gmx.de>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 */

#ifndef _PATCH_H
#define _PATCH_H

#include "units.h"
#include "midi_event.h"
#include "util.h"

#include <vector>
#include <boost/shared_ptr.hpp>


class Patch
{
  public:
    class Module;
    typedef boost::shared_ptr<Module> ModulePtr;
    typedef boost::shared_ptr<Unit> UnitPtr;

    Patch() {
        DEBUG_FN();
    }

    ~Patch() {
        DEBUG_FN();
    }

    void set_start(ModulePtr start) {
        _start = start;
    }

    void process(const MidiEvent & ev);
    void process_recursive(Module & m, MidiEvent & ev);


    class Input
      : public Unit
    {
      public:
        Input() { }

        virtual bool process(MidiEvent & ev) {
            return true;
        }
    };

    class Output
      : public Unit
    {
      public:
        Output() { }

        virtual bool process(MidiEvent & ev);
    };


    class Module
    {
      public:
        Module(UnitPtr unit)
          : _unit(unit) {
            DEBUG_FN();
        }

        ~Module() {
            DEBUG_FN();
        }

        void attach(ModulePtr m) { _next.push_back(m); }

        Unit & unit() { return *_unit; }
        std::vector<ModulePtr> & next() { return _next; }

      private:
        UnitPtr _unit;
        std::vector<ModulePtr> _next;
    };

  private:
    ModulePtr _start;
};


#endif // _PATCH_H
